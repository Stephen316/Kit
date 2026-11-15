import ctypes
from ctypes import wintypes

import win32job
from winerror import ERROR_MORE_DATA

from WindowsApi import KERNEL

MEMBER_LIMIT = 64
SNAPSHOT_ATTEMPTS = 3


class JobProcessIds(ctypes.Structure):
    _fields_ = [
        ("assigned", wintypes.DWORD),
        ("returned", wintypes.DWORD),
        ("ids", ctypes.c_size_t * MEMBER_LIMIT),
    ]


QUERY_MEMBERS = KERNEL.QueryInformationJobObject
QUERY_MEMBERS.argtypes = [
    wintypes.HANDLE,
    ctypes.c_int,
    ctypes.POINTER(JobProcessIds),
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
]
QUERY_MEMBERS.restype = wintypes.BOOL


def observed_members(job):
    # the native header distinguishes counted processes from actual populated ids
    for _ in range(SNAPSHOT_ATTEMPTS):
        data = JobProcessIds()
        success = QUERY_MEMBERS(
            int(job),
            win32job.JobObjectBasicProcessIdList,
            ctypes.byref(data),
            ctypes.sizeof(data),
            None,
        )
        if not success:
            error = ctypes.get_last_error()
            if error != ERROR_MORE_DATA:
                raise ctypes.WinError(error)
        if data.assigned > MEMBER_LIMIT or data.returned > MEMBER_LIMIT:
            raise OSError("offline calibration process tree exceeds its declared limit")
        if data.returned > data.assigned:
            raise OSError("Windows calibration job membership counts disagree")
        if success and data.returned == data.assigned:
            ids = tuple(data.ids[: data.returned])
            if 0 in ids or len(ids) != len(set(ids)):
                raise OSError(
                    "Windows calibration job membership contains invalid process ids"
                )
            return ids
    return None
