import inspect
import logging
import multiprocessing
import os
import shutil
import sys
import tempfile
import threading
import time
from io import TextIOWrapper
from logging import Logger
from queue import Queue
from types import MethodType
from typing import Any, Optional, List, Union, ContextManager

from larakit import StatefulNamespace


def mp_apply(generator, fn, *, pool_init=None, pool_init_args=None,
             batch_size: int = 1, ordered: bool = True, threads: int = None):
    cores = threads or multiprocessing.cpu_count()

    def loader(generator_, jobs_):
        for args in generator_:
            jobs_.put(args, block=True)
        jobs_.put(None, block=True)

    jobs = Queue(maxsize=cores * batch_size)
    loader_thread = threading.Thread(target=loader, args=(generator, jobs), daemon=True)

    loader_thread.start()

    with multiprocessing.Pool(initializer=pool_init, initargs=pool_init_args, processes=cores) as pool:
        imap_f = pool.imap if ordered else pool.imap_unordered

        yield from imap_f(fn, iter(jobs.get, None), chunksize=batch_size)

    loader_thread.join()


def step(description: str):
    def decorator(method):
        _, line_no = inspect.getsourcelines(method)
        return PipelineActivity.Step(method, line_no, description)

    return decorator


class SkipException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class StopException(KeyboardInterrupt):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def _pp_time(elapsed):
    elapsed = int(elapsed)
    parts = []

    if elapsed > 86400:  # days
        d = int(elapsed / 86400)
        elapsed -= d * 86400
        parts.append(f'{d}d')
    if elapsed > 3600:  # hours
        h = int(elapsed / 3600)
        elapsed -= h * 3600
        parts.append(f'{h}h')
    if elapsed > 60:  # minutes
        m = int(elapsed / 60)
        elapsed -= m * 60
        parts.append(f'{m}m')
    parts.append(f'{elapsed}s')
    return ' '.join(parts)


class PipelineActivity:
    class Step:
        def __init__(self, f: MethodType, line_no: int, description: str):
            self.id: str = f.__name__.strip('_')
            self.name: str = f.__name__
            self.declaring_class: str = f.__qualname__.split('.')[0]
            self._description: str = description
            self._line_no: int = line_no
            self._f: MethodType = f

            sig = inspect.signature(f)
            self.arg_count: int = len([
                param for param in sig.parameters.values()
                if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD)
            ]) - 1  # subtract 1 for 'self'

        def __lt__(self, other: 'PipelineActivity.Step') -> bool:
            return self._line_no < other._line_no

        def invoke(self, activity: 'PipelineActivity', input_path: Optional[str], output_path: Optional[str]):
            if self.arg_count == 1:
                self._f(activity, input_path)
            else:
                self._f(activity, input_path, output_path)

        def __str__(self) -> str:
            return self._description

        def __repr__(self) -> str:
            return f'Step(line={self._line_no}, id={self.id}, desc={self._description})'

    @classmethod
    def steps(cls) -> List['PipelineActivity.Step']:
        return sorted([method for _, method in inspect.getmembers(cls)
                       if isinstance(method, PipelineActivity.Step) and method.declaring_class == cls.__name__])

    def __init__(self, args, *, extra_argv=None, input_path: str = None, output_path: str = None, wdir: str = None,
                 log_file: Union[str, TextIOWrapper] = None, start_step: int = None, delete_on_exit: bool = True):
        self.args = args
        self.extra_argv = extra_argv
        self.delete_on_exit: bool = delete_on_exit
        self._input_path: Optional[str] = input_path
        self._output_path: Optional[str] = output_path

        # Configuring working dir
        if wdir is None:
            _wdir = _temp_dir = tempfile.mkdtemp(prefix='elo_tmp_')
        else:
            _wdir = wdir
            _temp_dir = None

        self._wdir: str = _wdir
        self._temp_dir: Optional[str] = _temp_dir

        if not os.path.isdir(self._wdir):
            os.makedirs(self._wdir)

        # Configuring logging file
        self._close_log_on_exit: bool = False

        self.log_file = log_file or os.path.join(self._wdir, self.__class__.__name__ + '.log')

        if isinstance(self.log_file, str):
            # pylint:disable=consider-using-with
            _log_fobj = open(self.log_file, 'ab')
            self._close_log_on_exit = True
        else:
            _log_fobj = self.log_file

        self._log_fobj: TextIOWrapper = _log_fobj

        logging.basicConfig(format='%(asctime)-15s [%(levelname)s] - %(message)s',
                            level=logging.INFO, stream=self._log_fobj)
        self._logger: Logger = logging.getLogger(type(self).__name__)

        # Resuming state
        self._steps: List['PipelineActivity.Step'] = self.steps()
        self.state: StatefulNamespace = StatefulNamespace(os.path.join(self._wdir, 'state.json'), autosave=False,
                                                          step_no=-1)

        if start_step is not None:
            self.state.step_no = start_step

    @property
    def log_fobj(self) -> TextIOWrapper:
        return self._log_fobj

    def wdir(self, *paths: str, create_if_not_exists: bool = True) -> str:
        path = os.path.abspath(os.path.join(self._wdir, *paths))
        if create_if_not_exists and not os.path.isdir(path):
            os.makedirs(path)

        return path

    def native_logging(self, stream=sys.stderr) -> ContextManager[Any]:
        class _NativeLogger:
            def __init__(self, from_fd, to_fd):
                self._from_fd = from_fd
                self._to_fd = to_fd
                self._bak_fd = None

            def __enter__(self):
                self._bak_fd = os.dup(self._from_fd)
                os.dup2(self._to_fd, self._from_fd)
                return self

            def __exit__(self, *args):
                os.dup2(self._bak_fd, self._from_fd)

        return _NativeLogger(stream.fileno(), self._log_fobj.fileno())

    def _index_of_step(self, step_id: str) -> Optional[int]:
        for i, s in enumerate(self._steps):
            if s.id == step_id:
                return i
        return None

    def _remove_step(self, step_id: str) -> None:
        idx = self._index_of_step(step_id)
        if idx is not None:
            del self._steps[idx]

    def save_state(self) -> None:
        self.state.save()

    def run(self) -> None:
        try:
            self.state.pipeline = self.state.pipeline or []

            for i, current_step in enumerate(self._steps):
                step_desc = f'({i + 1}/{len(self._steps)}) {current_step}...'

                print(f'{step_desc:<65s}', end='', flush=True)

                if self.state.step_no < i:
                    self._run_step(i, current_step)
                    self.state.step_no = i
                    self.save_state()
                else:
                    print('SKIPPED', flush=True)

            if self.delete_on_exit:
                shutil.rmtree(self._wdir, ignore_errors=True)
        finally:
            if self._log_fobj is not None and self._close_log_on_exit:
                self._log_fobj.close()
            if self._temp_dir is not None and os.path.isdir(self._temp_dir):
                shutil.rmtree(self._temp_dir, ignore_errors=True)

    def _run_step(self, i, current_step):
        try:
            self._logger.info('Step "%s" started', current_step.id)
            begin = time.time()

            input_path = self._input_path if len(self.state.pipeline) == 0 else self.state.pipeline[-1]
            output_path = None
            if current_step.arg_count > 1:
                if i == len(self._steps) - 1 and self._output_path:
                    if os.path.exists(self._output_path):
                        shutil.rmtree(self._output_path)
                    os.makedirs(self._output_path)

                    output_path = self._output_path
                else:
                    output_path = self.wdir(f'step_{current_step.name}')

            current_step.invoke(self, input_path, output_path)

            if output_path is not None:
                self.state.pipeline.append(output_path)

            elapsed_time = time.time() - begin
            self._logger.info('Step "%s" completed in %s', current_step.id, _pp_time(elapsed_time))

            print(f'DONE in {_pp_time(elapsed_time)}', flush=True)
        except SkipException:
            self._logger.info('Step "%s" skipped', current_step.id)
            print('SKIPPED', flush=True)
