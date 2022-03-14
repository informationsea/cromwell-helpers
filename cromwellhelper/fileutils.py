import os
import os.path
import typing


def realpath(path: str) -> str:
    if not path or path == '/':
        return path
    while os.path.islink(path):
        path = readlink_abs(path)
    return os.path.join(realpath(os.path.dirname(path)),
                        os.path.basename(path))


def readlink_abs(path: str) -> str:
    return os.path.abspath(
        os.path.join(os.path.dirname(path), os.readlink(path)))


def create_relative_symlink(src: str, dest: str):
    relpath = os.path.relpath(src, os.path.dirname(dest))
    os.symlink(relpath, dest)


def search_symlinks(path: str) -> typing.List[typing.Tuple[str, str, str]]:
    path = os.path.abspath(path)

    link_list = list()

    for root, _dirs, files in os.walk(path):
        for one_file in files:
            one_path = os.path.join(root, one_file)
            if os.path.islink(one_path):
                link_list.append(
                    (one_path, readlink_abs(one_path), realpath(one_path)))

    return link_list
