from contextlib import ExitStack, contextmanager
import ctypes
from ctypes import wintypes
import errno
import msvcrt
import os
from pathlib import Path
import stat

_GENERIC_READ = 0x80000000
_GENERIC_WRITE = 0x40000000
_FILE_SHARE_READ = 1
_OPEN_EXISTING = 3
_OPEN_ALWAYS = 4
_OPEN_REPARSE = 0x00200000
_BACKUP_SEMANTICS = 0x02000000
_FILE_TYPE_DISK = 1
_FILE_BASIC_INFO = 0
_FILE_ID_INFO = 18
_MISSING = {2, 3}
_SHARING_VIOLATION = 32
_INVALID_HANDLE = ctypes.c_void_p(-1).value
_DIRECTORY = stat.FILE_ATTRIBUTE_DIRECTORY
_REPARSE = stat.FILE_ATTRIBUTE_REPARSE_POINT


class _HandleInfo(ctypes.Structure):
    _fields_ = [
        ("attributes", wintypes.DWORD),
        ("creation_time", wintypes.FILETIME),
        ("access_time", wintypes.FILETIME),
        ("write_time", wintypes.FILETIME),
        ("volume_serial", wintypes.DWORD),
        ("size_high", wintypes.DWORD),
        ("size_low", wintypes.DWORD),
        ("links", wintypes.DWORD),
        ("index_high", wintypes.DWORD),
        ("index_low", wintypes.DWORD),
    ]


class _BasicInfo(ctypes.Structure):
    _fields_ = [
        ("creation_time", ctypes.c_int64),
        ("access_time", ctypes.c_int64),
        ("write_time", ctypes.c_int64),
        ("change_time", ctypes.c_int64),
        ("attributes", wintypes.DWORD),
    ]


class _FileId(ctypes.Structure):
    _fields_ = [
        ("volume_serial", ctypes.c_uint64),
        ("identifier", ctypes.c_ubyte * 16),
    ]


class _NativeError(OSError):
    def __init__(self):
        code = ctypes.get_last_error()
        super().__init__(f"Win32 error {code}")
        self.winerror = code


_KERNEL = ctypes.WinDLL("kernel32", use_last_error=True)


def _bind(name, result, *arguments):
    function = getattr(_KERNEL, name)
    function.argtypes = arguments
    function.restype = result
    return function


_CREATE_FILE = _bind(
    "CreateFileW",
    wintypes.HANDLE,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
)
_CLOSE_HANDLE = _bind("CloseHandle", wintypes.BOOL, wintypes.HANDLE)
_GET_TYPE = _bind("GetFileType", wintypes.DWORD, wintypes.HANDLE)
_GET_INFO = _bind(
    "GetFileInformationByHandle", wintypes.BOOL, wintypes.HANDLE, ctypes.POINTER(_HandleInfo)
)
_GET_EXTENDED = _bind(
    "GetFileInformationByHandleEx",
    wintypes.BOOL,
    wintypes.HANDLE,
    ctypes.c_int,
    wintypes.LPVOID,
    wintypes.DWORD,
)


def _open_native(path, access, share, disposition, extra_flags=0):
    handle = _CREATE_FILE(
        str(path), access, share, None, disposition, _OPEN_REPARSE | extra_flags, None
    )
    if handle == _INVALID_HANDLE or handle is None:
        raise _NativeError()
    return handle


def _close_native(handle):
    if not _CLOSE_HANDLE(handle):
        raise _NativeError()


def _handle_info(handle):
    info = _HandleInfo()
    if not _GET_INFO(handle, ctypes.byref(info)):
        raise _NativeError()
    return info


def _extended_info(handle, kind, info):
    if not _GET_EXTENDED(handle, kind, ctypes.byref(info), ctypes.sizeof(info)):
        raise _NativeError()
    return info


def _regular_handle(handle, message):
    if _GET_TYPE(handle) != _FILE_TYPE_DISK:
        raise ValueError(message)
    info = _handle_info(handle)
    if info.attributes & (_DIRECTORY | _REPARSE) or info.links != 1:
        raise ValueError(message)
    return info


def _record_identity(handle):
    info = _regular_handle(
        handle, "application record must be a regular file with one link and no reparse point"
    )
    identity = _extended_info(handle, _FILE_ID_INFO, _FileId())
    times = _extended_info(handle, _FILE_BASIC_INFO, _BasicInfo())
    file_id = bytes(identity.identifier)
    if not any(file_id) or times.change_time <= 0:
        raise ValueError("application record lacks native file identity or change time")
    if times.attributes & (_DIRECTORY | _REPARSE):
        raise ValueError("application record attributes changed during its native snapshot")
    return (
        identity.volume_serial,
        file_id,
        info.links,
        (info.size_high << 32) | info.size_low,
        times.creation_time,
        times.write_time,
        times.change_time,
        info.attributes,
        times.attributes,
    )


def _path_identity(path):
    handle = _open_native(path, _GENERIC_READ, _FILE_SHARE_READ, _OPEN_EXISTING)
    try:
        return _record_identity(handle)
    finally:
        _close_native(handle)


def shared_identity(info):
    return (
        info.st_dev,
        info.st_ino,
        stat.S_IFMT(info.st_mode),
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_birthtime_ns,
        info.st_file_attributes,
    )


def handle_identity(info):
    return (*shared_identity(info), info.st_ctime_ns)


def regular(info):
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or info.st_file_attributes & _REPARSE
    ):
        raise ValueError(
            "application record must be a regular file with one link and no reparse point"
        )


@contextmanager
def hold_directory(directory):
    directory = Path(os.path.abspath(directory))
    if directory.anchor.startswith("\\\\"):
        raise ValueError("application records require a local Windows volume")
    with ExitStack() as stack:
        ancestor = Path(directory.anchor)
        for part in ("", *directory.parts[1:]):
            ancestor /= part
            handle = _open_native(
                ancestor, 0, _FILE_SHARE_READ, _OPEN_EXISTING, _BACKUP_SEMANTICS
            )
            stack.callback(_close_native, handle)
            attributes = _handle_info(handle).attributes
            if not attributes & _DIRECTORY or attributes & _REPARSE:
                raise ValueError(
                    "application ancestor must be a directory without a reparse point"
                )
        yield


@contextmanager
def open_owner_lock(path):
    path = Path(os.path.abspath(path))
    try:
        with hold_directory(path.parent):
            try:
                handle = _open_native(path, _GENERIC_READ | _GENERIC_WRITE, 0, _OPEN_ALWAYS)
            except _NativeError as error:
                if error.winerror == _SHARING_VIOLATION:
                    raise BlockingIOError(
                        "another application process holds the endpoint lock"
                    ) from error
                raise
            try:
                _regular_handle(
                    handle, "application lock must be a regular file with one link"
                )
                yield
            finally:
                _close_native(handle)
    except _NativeError as error:
        raise OSError(f"Windows application lock failed: {error.winerror}") from error


@contextmanager
def open_record(path):
    path = Path(os.path.abspath(path))
    handle_opened = False
    try:
        with hold_directory(path.parent):
            handle = _open_native(path, _GENERIC_READ, _FILE_SHARE_READ, _OPEN_EXISTING)
            handle_opened = True
            try:
                opened = _record_identity(handle)
                if opened != _path_identity(path):
                    raise ValueError("application input changed while opening")
                descriptor = msvcrt.open_osfhandle(
                    handle, os.O_RDONLY | os.O_NOINHERIT | os.O_BINARY
                )
            except BaseException:
                _close_native(handle)
                raise
            try:
                source = os.fdopen(descriptor, "rb")
            except BaseException:
                os.close(descriptor)
                raise
            with source:
                yield source
                if opened != _record_identity(handle) or opened != _path_identity(path):
                    raise ValueError("application input changed while reading")
    except _NativeError as error:
        if not handle_opened and error.winerror in _MISSING:
            raise FileNotFoundError(
                errno.ENOENT, "Windows application record not found", str(path), error.winerror
            ) from error
        raise OSError(f"Windows application record failed: {error.winerror}") from error
