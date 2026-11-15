import os
from contextlib import ExitStack, contextmanager
from pathlib import Path

import msvcrt
import pywintypes
import win32con
import win32file

from OutputFiles import identity, regular


@contextmanager
def open_output(root, relative):
    root = Path(os.path.abspath(root))
    if root.anchor.startswith("\\\\"):
        raise ValueError("output intake requires a local Windows volume")
    try:
        with ExitStack() as stack:
            path = Path(root.anchor)
            for part in ("", *root.parts[1:], *relative.split("/")[:-1]):
                path /= part
                handle = win32file.CreateFile(str(path), 0, win32con.FILE_SHARE_READ, None, win32con.OPEN_EXISTING, win32con.FILE_FLAG_BACKUP_SEMANTICS | win32con.FILE_FLAG_OPEN_REPARSE_POINT, None)
                stack.callback(handle.Close)
                attributes = win32file.GetFileInformationByHandle(handle)[0]
                if not attributes & win32con.FILE_ATTRIBUTE_DIRECTORY or attributes & win32con.FILE_ATTRIBUTE_REPARSE_POINT:
                    raise ValueError("output ancestor must be a directory without a reparse point")
            path /= relative.split("/")[-1]
            handle = win32file.CreateFile(str(path), win32con.GENERIC_READ, win32con.FILE_SHARE_READ, None, win32con.OPEN_EXISTING, win32con.FILE_FLAG_OPEN_REPARSE_POINT, None)
            try:
                attributes = win32file.GetFileInformationByHandle(handle)[0]
                if attributes & (win32con.FILE_ATTRIBUTE_DIRECTORY | win32con.FILE_ATTRIBUTE_REPARSE_POINT):
                    raise ValueError("output must be a regular file without a reparse point")
                descriptor = msvcrt.open_osfhandle(int(handle), os.O_RDONLY | os.O_NOINHERIT | os.O_BINARY)
                handle.Detach()
                handle = None
            finally:
                if handle is not None:
                    handle.Close()
            source = stack.enter_context(os.fdopen(descriptor, "rb"))
            opened = os.fstat(source.fileno())
            regular(opened)
            if identity(opened) != identity(path.stat(follow_symlinks=False)):
                raise ValueError("output changed while it was opened")
            yield source
            if identity(opened) != identity(os.fstat(source.fileno())) or identity(opened) != identity(path.stat(follow_symlinks=False)):
                raise ValueError("output changed during intake")
    except pywintypes.error as error:
        raise OSError(f"Windows output intake failed: {error.winerror}") from error
