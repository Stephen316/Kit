import pywintypes
import win32api
import win32process


def worker_peak_working_set():
    try:
        return win32process.GetProcessMemoryInfo(win32api.GetCurrentProcess())[
            "PeakWorkingSetSize"
        ]
    except pywintypes.error as error:
        raise OSError("Windows decoder peak working set unavailable") from error
