# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from contextlib import contextmanager
import ctypes
from ctypes import wintypes
from pathlib import Path
import re
from threading import Lock

from WindowsIdentity import (
    CLOSE_HANDLE,
    EQUAL_SID,
    GET_CURRENT_PROCESS,
    GET_PROCESS_TIMES,
    KERNEL,
    OPEN_PROCESS,
    PROCESS_QUERY_LIMITED_INFORMATION,
    SYNCHRONIZE,
    WAIT_FOR_OBJECT,
    WAIT_OBJECT_0,
    WAIT_TIMEOUT,
    creation_time,
    token_owner,
)

# a kernel process handle fixes the process identifier through termination
GET_PROCESS_ID = KERNEL.GetProcessId
GET_PROCESS_ID.argtypes = [wintypes.HANDLE]
GET_PROCESS_ID.restype = wintypes.DWORD

# the held process image ties the watch to the intended executable
QUERY_IMAGE = KERNEL.QueryFullProcessImageNameW
QUERY_IMAGE.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
]
QUERY_IMAGE.restype = wintypes.BOOL

# the process code is meaningful only after the exact handle signals
GET_EXIT_CODE = KERNEL.GetExitCodeProcess
GET_EXIT_CODE.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
GET_EXIT_CODE.restype = wintypes.BOOL


# an unarmed identity must never be mistaken for an observed exit
class PeerUnavailable(ValueError):
    pass


# retaining the watch object prevents a wait from acquiring another process by pid
class ExitWatch:
    # a closed watch must not supply a potentially recycled handle value
    def __init__(self, handle, pid, started):
        self._lock = Lock()
        self.handle = handle
        self.pid = pid
        self.started = started


# the image query must describe the retained live kernel handle
def executable_path(handle):
    path = ctypes.create_unicode_buffer(32768)
    size = wintypes.DWORD(len(path))
    if not QUERY_IMAGE(handle, 0, path, ctypes.byref(size)):
        raise ctypes.WinError(ctypes.get_last_error())
    return Path(path.value).resolve(strict=True)


# session and sid checks reuse the token from the same process handle
def is_peer_owner(handle):
    user, session = token_owner(handle)
    caller, caller_session = token_owner(GET_CURRENT_PROCESS())
    user_sid = ctypes.cast(user, ctypes.POINTER(ctypes.c_void_p)).contents
    caller_sid = ctypes.cast(caller, ctypes.POINTER(ctypes.c_void_p)).contents
    return session == caller_session and bool(EQUAL_SID(user_sid, caller_sid))


# an invalid or signaled handle cannot establish the original live peer
def require_live(handle):
    status = WAIT_FOR_OBJECT(handle, 0)
    if status == WAIT_OBJECT_0:
        raise PeerUnavailable("Windows process exited before the watch was armed")
    if status != WAIT_TIMEOUT:
        raise ctypes.WinError(ctypes.get_last_error())


# the observer accepts only the lifetime already pinned by its caller
@contextmanager
def watch_peer(peer, executable):
    if not isinstance(peer, dict) or set(peer) != {"pid", "started"}:
        raise ValueError("expected an exact Windows peer identity")
    pid, started = peer["pid"], peer["started"]
    if (
        type(pid) is not int
        or not 0 < pid <= 0xFFFFFFFF
        or not isinstance(started, str)
        or not re.fullmatch(r"windows:[1-9][0-9]{0,19}", started)
    ):
        raise ValueError("expected a Windows PID and creation FILETIME")
    image = Path(executable)
    if not image.is_absolute():
        raise ValueError("expected an absolute executable path")
    image = image.resolve(strict=True)
    handle = OPEN_PROCESS(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
    if not handle:
        raise PeerUnavailable("exact Windows process handle is unavailable") from (
            ctypes.WinError(ctypes.get_last_error())
        )
    watch = ExitWatch(handle, pid, started)
    try:
        require_live(handle)
        if GET_PROCESS_ID(handle) != pid or creation_time(handle) != started:
            raise ValueError("Windows process creation identity differs")
        if executable_path(handle) != image or not is_peer_owner(handle):
            raise ValueError("Windows process image or owner session differs")
        require_live(handle)
        yield watch
    finally:
        with watch._lock:
            watch.handle = None
            if not CLOSE_HANDLE(handle):
                raise ctypes.WinError(ctypes.get_last_error())


# filetime words retain the exact kernel tick without a wall clock conversion
def filetime_ticks(value):
    return (value.dwHighDateTime << 32) | value.dwLowDateTime


# read the exit state only after the already owned handle has signaled
def observe_exit(watch, timeout_ms):
    if type(timeout_ms) is not int or not 0 <= timeout_ms <= 300_000:
        raise ValueError(
            "Windows exit wait must be between zero and 300000 milliseconds"
        )
    with watch._lock:
        handle = watch.handle
        if handle is None:
            raise ValueError("Windows process exit watch is closed")
        status = WAIT_FOR_OBJECT(handle, timeout_ms)
        if status == WAIT_TIMEOUT:
            return None
        if status != WAIT_OBJECT_0:
            raise ctypes.WinError(ctypes.get_last_error())
        times = [wintypes.FILETIME() for _ in range(4)]
        code = wintypes.DWORD()
        if not GET_PROCESS_TIMES(handle, *[ctypes.byref(value) for value in times]):
            raise ctypes.WinError(ctypes.get_last_error())
        if not GET_EXIT_CODE(handle, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        exited = filetime_ticks(times[1])
        if (
            GET_PROCESS_ID(handle) != watch.pid
            or f"windows:{filetime_ticks(times[0])}" != watch.started
            or exited == 0
        ):
            raise ValueError("Windows exit did not preserve the exact armed lifetime")
        return {
            "observation": "windows_process_exit_handle",
            "pid": watch.pid,
            "started": watch.started,
            "exit_filetime": exited,
            "exit_code": code.value,
        }
