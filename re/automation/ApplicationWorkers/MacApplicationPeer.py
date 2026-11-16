import ctypes
import os
import sys
from pathlib import Path

if __name__ != "__kit_pinned_application__":
    from ApplicationProtocol import require

PROC_PIDTBSDINFO = 3
PROC_FLAG_INEXIT = 4
PROC_SZOMB = 5
PATH_BUFFER_SIZE = 4096


class ProcBsdInfo(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_uint32),
        ("status", ctypes.c_uint32),
        ("exit_status", ctypes.c_uint32),
        ("pid", ctypes.c_uint32),
        ("parent_pid", ctypes.c_uint32),
        ("effective_uid", ctypes.c_uint32),
        ("effective_gid", ctypes.c_uint32),
        ("real_uid", ctypes.c_uint32),
        ("real_gid", ctypes.c_uint32),
        ("saved_uid", ctypes.c_uint32),
        ("saved_gid", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32),
        ("command", ctypes.c_char * 16),
        ("name", ctypes.c_char * 32),
        ("files", ctypes.c_uint32),
        ("process_group", ctypes.c_uint32),
        ("job_control", ctypes.c_uint32),
        ("terminal_device", ctypes.c_uint32),
        ("terminal_process_group", ctypes.c_uint32),
        ("nice", ctypes.c_int32),
        ("started_seconds", ctypes.c_uint64),
        ("started_microseconds", ctypes.c_uint64),
    ]


def pid_generation(read_info, pid, uid):
    info = ProcBsdInfo()
    size = ctypes.sizeof(info)
    require(
        read_info(pid, PROC_PIDTBSDINFO, 0, ctypes.byref(info), size) == size
        and info.pid == pid
        and info.real_uid == info.effective_uid == uid
        and not info.flags & PROC_FLAG_INEXIT
        and info.status != PROC_SZOMB
        and info.started_seconds > 0
        and 0 <= info.started_microseconds < 1_000_000,
        "macOS process exited, changed owner, or has no stable identity",
    )
    return info.started_seconds * 1_000_000 + info.started_microseconds


def process_peer(pid):
    require(
        sys.platform == "darwin", "macOS application peer verification requires macOS"
    )
    uid = os.getuid()
    require(
        type(pid) is int
        and 0 < pid <= (1 << 31) - 1
        and uid != 0
        and uid == os.geteuid(),
        "macOS application peer verification requires the unprivileged owner",
    )
    library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    read_info = library.proc_pidinfo
    read_info.argtypes = (
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint64,
        ctypes.c_void_p,
        ctypes.c_int,
    )
    read_info.restype = ctypes.c_int
    read_path = library.proc_pidpath
    read_path.argtypes = (ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32)
    read_path.restype = ctypes.c_int
    started = pid_generation(read_info, pid, uid)
    buffer = ctypes.create_string_buffer(PATH_BUFFER_SIZE)
    length = read_path(pid, buffer, len(buffer))
    path, terminator, _ = buffer.raw.partition(b"\0")
    require(
        0 < length == len(path) and terminator,
        "macOS process executable is unavailable",
    )
    executable = Path(os.fsdecode(path))
    require(
        executable.is_absolute() and pid_generation(read_info, pid, uid) == started,
        "macOS process changed while reading its executable",
    )
    return {
        "pid": pid,
        "uid": uid,
        "started_unix_microseconds": started,
        "executable": executable,
    }
