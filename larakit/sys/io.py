import os


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
