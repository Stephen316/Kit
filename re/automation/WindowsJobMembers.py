import ctypes
from ctypes import wintypes

import win32job
from winerror import ERROR_MORE_DATA

from WindowsApi import KERNEL

INITIAL_CAPACITY = 64
SNAPSHOT_ATTEMPTS = 3


class JobProcessIds(ctypes.Structure):
    _fields_ = [
        ("assigned", wintypes.DWORD),
        ("returned", wintypes.DWORD),
        ("ids", ctypes.c_size_t * 1),
    ]


QUERY_MEMBERS = KERNEL.QueryInformationJobObject
QUERY_MEMBERS.argtypes = [
    wintypes.HANDLE,
    ctypes.c_int,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
]
QUERY_MEMBERS.restype = wintypes.BOOL
PID_OFFSET = JobProcessIds.ids.offset
PID_SIZE = ctypes.sizeof(ctypes.c_size_t)


def query_members(job, capacity):
    size = PID_OFFSET + capacity * PID_SIZE
    if size > 0xFFFFFFFF:
        raise OSError("Windows job membership exceeds the native buffer size")
    buffer = ctypes.create_string_buffer(size)
    success = QUERY_MEMBERS(
        int(job),
        win32job.JobObjectBasicProcessIdList,
        ctypes.byref(buffer),
        size,
        None,
    )
    if not success:
        error = ctypes.get_last_error()
        if error != ERROR_MORE_DATA:
            raise ctypes.WinError(error)
    counts = JobProcessIds.from_buffer(buffer)
    if counts.returned > capacity or counts.returned > counts.assigned:
        raise OSError("Windows job membership counts disagree")
    return success, counts.assigned, counts.returned, buffer


def observed_members(job, *, member_limit=None):
    capacity = INITIAL_CAPACITY if member_limit is None else member_limit
    for _ in range(SNAPSHOT_ATTEMPTS):
        success, assigned, returned, buffer = query_members(job, capacity)
        if member_limit is not None and assigned > member_limit:
            raise OSError("offline calibration process tree exceeds its declared limit")
        if success and assigned == returned:
            raw_ids = (ctypes.c_size_t * returned).from_buffer(buffer, PID_OFFSET)
            ids = tuple(raw_ids)
            if 0 in ids or len(ids) != len(set(ids)):
                raise OSError("Windows job membership contains invalid process ids")
            return ids
        if member_limit is None and assigned > capacity:
            capacity = assigned
    return None


def has_job_members(job):
    # an incomplete list cannot prove that the owned job is empty
    success, assigned, returned, _ = query_members(job, 1)
    return not success or assigned != 0 or returned != 0
