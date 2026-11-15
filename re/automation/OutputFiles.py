import os
import stat
from contextlib import ExitStack, contextmanager
from pathlib import Path


def identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def regular(info):
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError("output must be a regular file with one link and no reparse point")


@contextmanager
def open_output(root, relative):
    if os.name == "nt":
        from WindowsOutputFiles import open_output as open_windows_output

        with open_windows_output(root, relative) as source:
            yield source
        return
    root = Path(os.path.abspath(root))
    with ExitStack() as stack:
        descriptor = os.open(root.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        stack.callback(os.close, descriptor)
        for part in (*root.parts[1:], *relative.split("/")[:-1]):
            descriptor = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            stack.callback(os.close, descriptor)
        name = relative.split("/")[-1]
        before = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        regular(before)
        file_descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
        source = stack.enter_context(os.fdopen(file_descriptor, "rb"))
        opened = os.fstat(source.fileno())
        regular(opened)
        if identity(before) != identity(opened):
            raise ValueError("output changed while it was opened")
        yield source
        if identity(opened) != identity(os.fstat(source.fileno())) or identity(opened) != identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False)):
            raise ValueError("output changed during intake")
