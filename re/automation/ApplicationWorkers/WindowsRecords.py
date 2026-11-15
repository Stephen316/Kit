import os
import stat
from contextlib import ExitStack, contextmanager
from pathlib import Path

import msvcrt
import pywintypes
import win32con
import win32file


def shared_identity(info):
    return (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode), info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_birthtime_ns, info.st_file_attributes)


def handle_identity(info):
    return (*shared_identity(info), info.st_ctime_ns)


def regular(info):
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_file_attributes & win32con.FILE_ATTRIBUTE_REPARSE_POINT:
        raise ValueError("application record must be a regular file with one link and no reparse point")


@contextmanager
def hold_directory(directory):
    directory = Path(os.path.abspath(directory))
    if directory.anchor.startswith("\\\\"):
        raise ValueError("application records require a local Windows volume")
    with ExitStack() as stack:
        ancestor = Path(directory.anchor)
        for part in ("", *directory.parts[1:]):
            ancestor /= part
            handle = win32file.CreateFile(str(ancestor), 0, win32con.FILE_SHARE_READ, None, win32con.OPEN_EXISTING, win32con.FILE_FLAG_BACKUP_SEMANTICS | win32file.FILE_FLAG_OPEN_REPARSE_POINT, None)
            stack.callback(handle.Close)
            attributes = win32file.GetFileInformationByHandle(handle)[0]
            if not attributes & win32con.FILE_ATTRIBUTE_DIRECTORY or attributes & win32con.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError("application ancestor must be a directory without a reparse point")
        yield


@contextmanager
def open_owner_lock(path):
    path = Path(os.path.abspath(path))
    try:
        with hold_directory(path.parent):
            try:
                handle = win32file.CreateFile(str(path), win32con.GENERIC_READ | win32con.GENERIC_WRITE, 0, None, win32con.OPEN_ALWAYS, win32file.FILE_FLAG_OPEN_REPARSE_POINT, None)
            except pywintypes.error as error:
                if error.winerror == 32:
                    raise BlockingIOError("another application process holds the endpoint lock") from error
                raise
            try:
                info = win32file.GetFileInformationByHandle(handle)
                if (info[0] & (win32con.FILE_ATTRIBUTE_DIRECTORY | win32con.FILE_ATTRIBUTE_REPARSE_POINT)
                        or info[7] != 1 or win32file.GetFileType(handle) != win32file.FILE_TYPE_DISK):
                    raise ValueError("application lock must be a regular file with one link and no reparse point")
                yield
            finally:
                handle.Close()
    except pywintypes.error as error:
        raise OSError(f"Windows application lock failed: {error.winerror}") from error


@contextmanager
def open_record(path):
    path = Path(os.path.abspath(path))
    try:
        with hold_directory(path.parent):
            handle = win32file.CreateFile(str(path), win32con.GENERIC_READ, win32con.FILE_SHARE_READ, None, win32con.OPEN_EXISTING, win32file.FILE_FLAG_OPEN_REPARSE_POINT, None)
            try:
                attributes = win32file.GetFileInformationByHandle(handle)[0]
                if attributes & (win32con.FILE_ATTRIBUTE_DIRECTORY | win32con.FILE_ATTRIBUTE_REPARSE_POINT) or win32file.GetFileType(handle) != win32file.FILE_TYPE_DISK:
                    raise ValueError("application record must be a regular file without a reparse point")
                descriptor = msvcrt.open_osfhandle(int(handle), os.O_RDONLY | os.O_NOINHERIT | os.O_BINARY)
                handle.Detach()
                handle = None
            finally:
                if handle is not None:
                    handle.Close()
            with os.fdopen(descriptor, "rb") as source:
                opened = os.fstat(source.fileno())
                regular(opened)
                before = path.lstat()
                regular(before)
                if shared_identity(opened) != shared_identity(before):
                    raise ValueError("application input changed while opening")
                yield source
                after = os.fstat(source.fileno())
                final = path.lstat()
                regular(after)
                regular(final)
                if handle_identity(opened) != handle_identity(after) or shared_identity(opened) != shared_identity(final):
                    raise ValueError("application input changed while reading")
    except pywintypes.error as error:
        raise OSError(f"Windows application record failed: {error.winerror}") from error
