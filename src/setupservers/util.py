import errno
import os
import pathlib
import re
import socket
from contextlib import closing

import requests


def is_port_available(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.bind((host, port))
        except socket.error as e:
            return False
    return True


def find_free_port(host, port: int):
    if is_port_available(host, port):
        return port
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind((host, 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def docker_container_name(module_name: str, work_dir: pathlib.Path):
    split = module_name.split('.')
    name = split[0]

    work_path_string = str(work_dir.parent)
    pattern = re.compile(r'([a-zA-Z]+)')
    for (letters) in re.findall(pattern, work_path_string):
        name += "." + letters[0]

    name += '_' + work_dir.name + '_' + '_'.join(split[1:])
    name = re.sub('[^a-zA-Z0-9_.-]', '_', name)
    name = re.sub('__+', '_', name)
    return name


def download_file(url, to_path: pathlib.Path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(to_path, 'wb') as f:
            f.write(response.raw.read())
    else:
        raise Exception(str(response))


def unpack_targz(file: pathlib.Path, to_dir_path: pathlib.Path):
    import tarfile
    if file.name.endswith("tar.gz"):
        with tarfile.open(file, "r:gz") as tar:
            tar.extractall(path=to_dir_path)
    elif file.name.endswith("tar"):
        with tarfile.open(file, "r:") as tar:
            tar.extractall(path=to_dir_path)


def pid_exists(pid):
    """Check whether pid exists in the current process table.
    UNIX only.
    """
    if pid < 0:
        return False
    if pid == 0:
        # According to "man 2 kill" PID 0 refers to every process
        # in the process group of the calling process.
        # On certain systems 0 is a valid PID but we have no way
        # to know that in a portable fashion.
        raise ValueError('invalid PID 0')
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True
