import atexit
import logging
import os
import re
import shutil
import subprocess
import unicodedata
from collections.abc import Callable
from typing import BinaryIO, Generator, List, Union, IO, Dict, Tuple, Optional

DEVNULL = open(os.devnull, 'wb')  # pylint:disable=consider-using-with
atexit.register(DEVNULL.close)


class ShellError(Exception):
    def __init__(self, command: str, err_no: int, message: str = None):
        self.command: str = command
        self.errno: int = err_no
        self.message: Optional[str] = message

    def __str__(self):
        string = f"Command '{self.command}' failed with exit code {self.errno}"
        if self.message is not None:
            string += ': ' + repr(self.message)
        return string

    def __repr__(self):
        return self.__str__()


def shexec(cmd: Union[str, List[str]], *, stdin: Union[str, IO] = None,
           stdout: IO = subprocess.PIPE, stderr: IO = subprocess.PIPE, background: bool = False,
           env: Dict[str, str] = None, cwd: str = None) -> Union[Tuple[str, str], subprocess.Popen]:
    str_cmd = cmd if isinstance(cmd, str) else ' '.join(cmd)
    logging.getLogger('shell_exec').info(str_cmd)

    message = None
    if background:
        if stdout == subprocess.PIPE:
            stdout = DEVNULL
        if stderr == subprocess.PIPE:
            stderr = DEVNULL
    elif stdin is not None and isinstance(stdin, str):
        message = stdin
        stdin = subprocess.PIPE

    is_shell = isinstance(cmd, str)
    # pylint:disable=consider-using-with
    process = subprocess.Popen(cmd, stdin=stdin, stdout=stdout, stderr=stderr, shell=is_shell, env=env, cwd=cwd)

    stdout_dump = None
    stderr_dump = None
    return_code = 0

    if message is not None or stdout == subprocess.PIPE or stderr == subprocess.PIPE:
        stdout_dump, stderr_dump = process.communicate(message)
        return_code = process.returncode
    elif not background:
        return_code = process.wait()

    if background:
        return process

    if stdout_dump is not None:
        stdout_dump = stdout_dump.decode('utf-8')
    if stderr_dump is not None:
        stderr_dump = stderr_dump.decode('utf-8')

    if return_code != 0:
        raise ShellError(str_cmd, return_code, stderr_dump)
    return stdout_dump, stderr_dump


def safe_open(path: str, mode: str = 'r', encoding: str = 'utf-8') -> Optional[IO]:
    if path is None:
        return None

    if 'w' in mode or 'a' in mode:
        folder = os.path.dirname(path)
        if not os.path.isdir(folder):
            os.makedirs(folder)
    elif not os.path.isfile(path):
        return None

    return open(path, mode=mode, encoding=encoding)


def sanitize_filename(filename: str, allow_unicode: bool = False) -> str:
    filename = str(filename).strip()

    if allow_unicode:
        filename = unicodedata.normalize('NFKC', filename)
    else:
        filename = (unicodedata.normalize('NFKD', filename)
                    .encode('ascii', 'ignore')
                    .decode('ascii'))

    return re.sub(r'[^\w\s\-.]', '_', filename)


def tail_1(path: str) -> bytes:
    file_size = os.path.getsize(path)

    window_size = 1024

    with open(path, 'rb') as file:
        while True:
            file.seek(-min(file_size, window_size), 2)
            last_line = file.read().rstrip(b'\n')

            if b'\n' in last_line:
                return last_line[last_line.rindex(b'\n') + 1:]
            if window_size >= file_size:
                return last_line
            window_size *= 2


def lc(filename: str, block_size: int = 65536) -> int:
    if not os.path.isfile(filename):
        raise FileNotFoundError(f'File "{filename}" does not exist.')

    def _blocks(files: BinaryIO) -> Generator[bytes, None, None]:
        while True:
            b = files.read(block_size)
            if not b:
                break
            yield b

    with open(filename, 'rb') as stream:
        count = 0
        for block in _blocks(stream):
            count += block.count(b'\n')
        return count


def cat(files: List[str], output: str, *, buffer_size: int = 10 * 1024 * 1024, append: bool = False):
    mode = 'wb' if not append else 'ab'
    with open(output, mode) as blob:
        for f in files:
            with open(f, 'rb') as source:
                shutil.copyfileobj(source, blob, buffer_size)


def link(file_path: str, dest_path: str, symbolic: bool = False, overwrite: bool = True) -> str:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File '{file_path}' does not exist.")

    if os.path.isdir(dest_path):
        dest_path = os.path.join(dest_path, os.path.basename(file_path))
    elif os.path.isfile(dest_path):
        if not overwrite:
            raise IOError(f"Destination path '{dest_path}' already exists.")
        os.remove(dest_path)
    else:
        dirname = os.path.dirname(dest_path)
        if not os.path.isdir(dirname):
            raise IOError(f"Destination directory '{dirname}' does not exist.")

    if symbolic:
        os.symlink(file_path, dest_path)
    else:
        os.link(file_path, dest_path)

    return dest_path


def tar_gz(output_archive: str, input_dir: str, *,
           file_filter: Callable[[str], bool] = None, use_pigz: bool = True) -> None:
    filenames = [f for f in os.listdir(input_dir) if file_filter is None or file_filter(os.path.join(input_dir, f))]

    cmd = ['tar', '-cf', output_archive]
    if use_pigz:
        cmd.append('--use-compress-program=pigz')
    cmd.extend(['--directory', input_dir])
    cmd.extend(filenames)

    shexec(cmd)


def nvidia_devices() -> List[int]:
    try:
        output, _ = shexec('nvidia-smi --query-gpu=index --format=csv,noheader,nounits')
        return [int(index) for index in output.splitlines()]
    except ShellError:
        return []


def nvidia_device_count() -> int:
    return len(nvidia_devices())


def nvidia_has_device() -> bool:
    return nvidia_device_count() > 0
