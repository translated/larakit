import atexit
import logging
import os
import subprocess
from typing import BinaryIO, Generator, List, Union, IO, Dict, Tuple, Optional

DEVNULL = open(os.devnull, 'wb')
atexit.register(DEVNULL.close)


class ShellError(Exception):
    def __init__(self, command: str, err_no: int, message: str = None):
        self.command: str = command
        self.errno: int = err_no
        self.message: Optional[str] = message

    def __str__(self):
        string = "Command '%s' failed with exit code %d" % (self.command, self.errno)
        if self.message is not None:
            string += ': ' + repr(self.message)
        return string

    def __repr__(self):
        return self.__str__()


def shexec(cmd: Union[str, List[str]], stdin: Union[str, IO] = None,
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
    else:
        if stdout_dump is not None:
            stdout_dump = stdout_dump.decode('utf-8')
        if stderr_dump is not None:
            stderr_dump = stderr_dump.decode('utf-8')

        if return_code != 0:
            raise ShellError(str_cmd, return_code, stderr_dump)
        else:
            return stdout_dump, stderr_dump


def gpu_devices() -> List[int]:
    try:
        output, _ = shexec('nvidia-smi --query-gpu=index --format=csv,noheader,nounits')
        return [int(index) for index in output.splitlines()]
    except ShellError:
        return []


def tail_1(path: str) -> bytes:
    file_size = os.path.getsize(path)

    window_size = 1024

    with open(path, 'rb') as file:
        while True:
            file.seek(-min(file_size, window_size), 2)
            last_line = file.read().rstrip(b'\n')

            if b'\n' in last_line:
                return last_line[last_line.rindex(b'\n') + 1:]
            elif window_size >= file_size:
                return last_line
            else:
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
