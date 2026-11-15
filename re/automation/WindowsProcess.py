import os
import secrets
import signal
import subprocess
import time

import pywintypes
import win32api
import win32con
import win32event
import win32job
import win32process

from ApplicationWorkers.WindowsIdentity import creation_time, process_start
from WindowsApi import KERNEL, create_suspended


JOBS = {}


class WindowsProcess:
    def __init__(self, argv, root, environment, stdout, stderr):
        self.handle = None
        self.job = None
        self.pid = None
        self.returncode = None
        self.peak_memory_bytes = 0
        self.job_name = f"Local\\KitResearch-{secrets.token_hex(24)}"
        info = None
        try:
            self.job = win32job.CreateJobObject(None, self.job_name)
            if win32api.GetLastError() == 183:
                self.job.Close()
                self.job = None
                raise OSError("session job object already exists")
            limits = win32job.QueryInformationJobObject(self.job, win32job.JobObjectExtendedLimitInformation)
            limits["BasicLimitInformation"]["LimitFlags"] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            win32job.SetInformationJobObject(self.job, win32job.JobObjectExtendedLimitInformation, limits)
            info = create_suspended(argv, root, environment, stdout, stderr, int(self.job))
            self.handle = info.process
            self.pid = int(info.pid)
            self.identity = creation_time(self.handle)
            if not win32job.IsProcessInJob(self.handle, self.job):
                raise OSError("runner was not created inside its session job")
            JOBS[self.pid] = self
            if win32process.ResumeThread(info.thread) != 1:
                raise OSError("runner thread did not resume from its initial suspension")
        except BaseException as error:
            try:
                if self.handle is not None and win32event.WaitForSingleObject(self.handle, 0) == win32event.WAIT_TIMEOUT:
                    win32process.TerminateProcess(self.handle, 1)
                if self.job is not None:
                    win32job.TerminateJobObject(self.job, 1)
                if self.handle is not None:
                    win32event.WaitForSingleObject(self.handle, 5000)
            finally:
                self.close()
            if isinstance(error, pywintypes.error):
                raise OSError(f"Windows runner setup failed: {error.winerror}") from error
            raise
        finally:
            if info is not None:
                KERNEL.CloseHandle(info.thread)

    def poll(self):
        if self.returncode is None and win32event.WaitForSingleObject(self.handle, 0) == win32event.WAIT_OBJECT_0:
            self.returncode = win32process.GetExitCodeProcess(self.handle)
            try:
                self.peak_memory_bytes = win32process.GetProcessMemoryInfo(self.handle)["PeakWorkingSetSize"]
            except pywintypes.error as error:
                if self.peak_memory_bytes == 0:
                    raise OSError("runner peak memory measurement unavailable") from error
        return self.returncode

    def wait(self, timeout=None):
        duration = win32event.INFINITE if timeout is None else max(0, int(timeout * 1000))
        if win32event.WaitForSingleObject(self.handle, duration) == win32event.WAIT_TIMEOUT:
            raise subprocess.TimeoutExpired("research runner", timeout)
        return self.poll()

    def finish(self):
        if self.poll() is None:
            return None
        win32job.TerminateJobObject(self.job, 1)
        until = time.monotonic() + 5
        while win32job.QueryInformationJobObject(self.job, win32job.JobObjectBasicProcessIdList):
            if time.monotonic() >= until:
                raise OSError("Windows job descendants did not terminate")
            time.sleep(0.01)
        return {"exit_status": self.returncode, "signal": None, "peak_memory_bytes": self.peak_memory_bytes}

    def signal(self, number):
        if number not in (signal.SIGTERM, 9):
            raise ValueError("Windows session stops accept only graceful or hard termination")
        if number == signal.SIGTERM:
            try:
                os.kill(self.pid, signal.CTRL_BREAK_EVENT)
                return True
            except OSError:
                return False
        win32job.TerminateJobObject(self.job, 1)
        return True

    def memory(self):
        total = 0
        for pid in win32job.QueryInformationJobObject(self.job, win32job.JobObjectBasicProcessIdList):
            try:
                handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ | win32con.SYNCHRONIZE, False, pid)
            except pywintypes.error as error:
                if error.winerror == 87:
                    continue
                raise OSError(f"session memory measurement failed: {error.winerror}") from error
            try:
                counters = win32process.GetProcessMemoryInfo(handle)
                total += counters["WorkingSetSize"]
                if pid == self.pid:
                    self.peak_memory_bytes = max(self.peak_memory_bytes, counters["PeakWorkingSetSize"])
            except pywintypes.error as error:
                if win32event.WaitForSingleObject(handle, 0) != win32event.WAIT_OBJECT_0:
                    raise OSError(f"session memory measurement failed: {error.winerror}") from error
            finally:
                handle.Close()
        return total

    def close(self):
        JOBS.pop(self.pid, None)
        if self.job is not None:
            self.job.Close()
            self.job = None
        if self.handle is not None:
            KERNEL.CloseHandle(self.handle)
            self.handle = None


def stop_orphan(pid, recorded, grace, job_name):
    if process_start(pid) != recorded:
        return False
    if not isinstance(job_name, str) or not job_name.startswith("Local\\KitResearch-"):
        raise OSError("session has no recorded Windows job identity")
    process = win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION | win32con.SYNCHRONIZE, False, pid)
    try:
        job = win32job.OpenJobObject(win32job.JOB_OBJECT_TERMINATE | win32job.JOB_OBJECT_QUERY, False, job_name)
        try:
            if creation_time(int(process)) != recorded or not win32job.IsProcessInJob(process, job):
                return False
            win32job.TerminateJobObject(job, 1)
            until = time.monotonic() + max(grace, 5)
            while time.monotonic() < until:
                if not win32job.QueryInformationJobObject(job, win32job.JobObjectBasicProcessIdList):
                    return True
                time.sleep(0.05)
            return False
        finally:
            job.Close()
    finally:
        process.Close()
