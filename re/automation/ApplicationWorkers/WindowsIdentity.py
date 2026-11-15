import ctypes
from ctypes import wintypes

KERNEL = ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SYNCHRONIZE = 0x00100000
ERROR_INVALID_PARAMETER = 87
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258

OPEN_PROCESS = KERNEL.OpenProcess
OPEN_PROCESS.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OPEN_PROCESS.restype = wintypes.HANDLE
WAIT_FOR_OBJECT = KERNEL.WaitForSingleObject
WAIT_FOR_OBJECT.argtypes = [wintypes.HANDLE, wintypes.DWORD]
WAIT_FOR_OBJECT.restype = wintypes.DWORD
CLOSE_HANDLE = KERNEL.CloseHandle
CLOSE_HANDLE.argtypes = [wintypes.HANDLE]
CLOSE_HANDLE.restype = wintypes.BOOL

GET_PROCESS_TIMES = KERNEL.GetProcessTimes
FILETIME_POINTER = ctypes.POINTER(wintypes.FILETIME)
GET_PROCESS_TIMES.argtypes = [
    wintypes.HANDLE,
    FILETIME_POINTER,
    FILETIME_POINTER,
    FILETIME_POINTER,
    FILETIME_POINTER,
]
GET_PROCESS_TIMES.restype = wintypes.BOOL


# token queries keep ownership checks independent of installed python extensions
ADVAPI = ctypes.WinDLL("advapi32", use_last_error=True)

# querying the token needs no impersonation or modification rights
TOKEN_QUERY = 0x0008

# the user class reports the sid of the primary token
TOKEN_USER = 1

# the session class distinguishes desktop sessions of the same owner
TOKEN_SESSION_ID = 12

# fixed space covers the native user header and maximum sid
TOKEN_USER_BYTES = 128

# the current process supplies the trusted owner and desktop session
GET_CURRENT_PROCESS = KERNEL.GetCurrentProcess
GET_CURRENT_PROCESS.argtypes = []
GET_CURRENT_PROCESS.restype = wintypes.HANDLE

# query access is sufficient for peer ownership without impersonation
OPEN_TOKEN = ADVAPI.OpenProcessToken
OPEN_TOKEN.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
OPEN_TOKEN.restype = wintypes.BOOL

# only the kernel token establishes the actual user and session
GET_TOKEN = ADVAPI.GetTokenInformation
GET_TOKEN.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
GET_TOKEN.restype = wintypes.BOOL

# native comparison avoids depending on account names or token buffer addresses
EQUAL_SID = ADVAPI.EqualSid
EQUAL_SID.argtypes = [wintypes.LPVOID, wintypes.LPVOID]
EQUAL_SID.restype = wintypes.BOOL


# both token values must come from the same process handle
def token_owner(handle):
    token = wintypes.HANDLE()
    if not OPEN_TOKEN(handle, TOKEN_QUERY, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        user = ctypes.create_string_buffer(TOKEN_USER_BYTES)
        session = wintypes.DWORD()
        size = wintypes.DWORD()
        if not GET_TOKEN(token, TOKEN_USER, user, ctypes.sizeof(user), ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not GET_TOKEN(token, TOKEN_SESSION_ID, ctypes.byref(session), ctypes.sizeof(session), ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        return user, session.value
    finally:
        if not CLOSE_HANDLE(token):
            raise ctypes.WinError(ctypes.get_last_error())


# fusion admission needs an exact live peer under the same local owner
def peer_matches(pid, started):
    if type(pid) is not int or not 0 < pid <= 0xFFFFFFFF:
        return False
    handle = OPEN_PROCESS(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
    if not handle:
        return False
    try:
        if WAIT_FOR_OBJECT(handle, 0) != WAIT_TIMEOUT or creation_time(handle) != started:
            return False
        peer_user, peer_session = token_owner(handle)
        owner_user, owner_session = token_owner(GET_CURRENT_PROCESS())
        peer_sid = ctypes.cast(peer_user, ctypes.POINTER(ctypes.c_void_p)).contents
        owner_sid = ctypes.cast(owner_user, ctypes.POINTER(ctypes.c_void_p)).contents
        return (peer_session == owner_session and bool(EQUAL_SID(peer_sid, owner_sid))
                and creation_time(handle) == started
                and WAIT_FOR_OBJECT(handle, 0) == WAIT_TIMEOUT)
    except OSError:
        return False
    finally:
        if not CLOSE_HANDLE(handle):
            raise ctypes.WinError(ctypes.get_last_error())


def creation_time(handle):
    times = [wintypes.FILETIME() for _ in range(4)]
    if not GET_PROCESS_TIMES(handle, *[ctypes.byref(value) for value in times]):
        raise ctypes.WinError(ctypes.get_last_error())
    created = times[0]
    return f"windows:{(created.dwHighDateTime << 32) | created.dwLowDateTime}"


def process_start(pid):
    # ctypes narrows a DWORD argument, so guard against aliasing another PID.
    if not 0 <= pid <= 0xFFFFFFFF:
        raise OverflowError("Windows process identifier is outside the DWORD range")
    handle = OPEN_PROCESS(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
    if not handle:
        error = ctypes.get_last_error()
        if error == ERROR_INVALID_PARAMETER:
            return None
        raise OSError(f"process identity measurement failed: {error}")
    try:
        status = WAIT_FOR_OBJECT(handle, 0)
        if status == WAIT_OBJECT_0:
            return None
        if status != WAIT_TIMEOUT:
            raise OSError("process identity wait failed")
        return creation_time(handle)
    finally:
        if not CLOSE_HANDLE(handle):
            raise ctypes.WinError(ctypes.get_last_error())
