import os
import time
from pathlib import Path

import pywintypes
import win32api
import win32con
import win32event
import win32job
import win32process

from CalibrationWindowsJob import observed_members
from Processes import KILL_SIGNAL
from Sessions import read_bounded
from Supervisor import set_pause
from WindowsApi import creation_time
from WindowsProcess import WindowsProcess


class CalibrationWindows(WindowsProcess):
    def __init__(self, command, root, directory, environment, stdout, stderr, pool):
        self.directory = directory
        self.pool = pool
        self.interpreter = None
        self.interpreter_path = directory / (
            "RecoveryInterpreter.json"
            if stderr is None
            else "SupervisorInterpreter.json"
        )
        environment.update(
            {
                key: os.environ[key]
                for key in ("SystemRoot", "WINDIR", "PATHEXT")
                if key in os.environ
            }
        )
        environment.update(
            {key: str(directory) for key in ("USERPROFILE", "TEMP", "TMP")}
        )
        environment["PYTHONUTF8"] = "1"
        command = [
            command[0],
            str(Path(__file__).with_name("CalibrationWindowsHost.py")),
            str(self.interpreter_path),
            *command[1:],
        ]
        duplicate = None if stderr is not None else os.dup(stdout)
        try:
            super().__init__(
                command,
                root,
                environment,
                stdout,
                stderr if duplicate is None else duplicate,
            )
        finally:
            if duplicate is not None:
                os.close(duplicate)

    def poll(self):
        if self.returncode is not None:
            return self.returncode
        try:
            status = win32event.WaitForSingleObject(self.handle, 0)
            if status == win32event.WAIT_OBJECT_0:
                self.returncode = win32process.GetExitCodeProcess(self.handle)
            elif status != win32event.WAIT_TIMEOUT:
                raise OSError("Windows calibration supervisor wait failed")
        except pywintypes.error as error:
            raise OSError(
                "Windows calibration supervisor status unavailable"
            ) from error
        return self.returncode

    def terminate(self):
        set_pause(
            {"state": self.directory / "State", "pools": {self.pool: {}}},
            self.pool,
            "calibration stopped",
        )

    def has_members(self):
        try:
            counts = win32job.QueryInformationJobObject(
                self.job, win32job.JobObjectBasicAccountingInformation
            )
            return counts["ActiveProcesses"] != 0
        except pywintypes.error as error:
            raise OSError("Windows calibration job membership unavailable") from error

    def bind_interpreter(self):
        try:
            record = read_bounded(self.interpreter_path)
        except FileNotFoundError:
            return
        pid, started = record["pid"], record["process_start"]
        if (
            type(pid) is not int
            or pid <= 1
            or (pid != self.pid and record["parent_pid"] != self.pid)
        ):
            raise OSError(
                "Windows supervisor interpreter is not the contained launcher or its child"
            )
        try:
            handle = win32api.OpenProcess(
                win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
        except pywintypes.error as error:
            if error.winerror == 87:
                return
            raise OSError(
                "Windows supervisor interpreter could not be opened"
            ) from error
        try:
            if started != creation_time(int(handle)) or not win32job.IsProcessInJob(
                handle, self.job
            ):
                raise OSError(
                    "Windows supervisor interpreter job identity cannot be verified"
                )
            self.interpreter = pid, started
        except pywintypes.error as error:
            raise OSError(
                "Windows supervisor interpreter job identity unavailable"
            ) from error
        finally:
            handle.Close()

    def sample_workers(self):
        if self.interpreter is None:
            self.bind_interpreter()
            if self.interpreter is None:
                return None
        members = observed_members(self.job)
        if members is None:
            return None
        return sum(self.member_working_set(pid) for pid in members if pid != self.pid)

    def member_working_set(self, pid):
        access = (
            win32con.PROCESS_QUERY_INFORMATION
            | win32con.PROCESS_VM_READ
            | win32con.SYNCHRONIZE
        )
        try:
            handle = win32api.OpenProcess(access, False, pid)
        except pywintypes.error as error:
            if error.winerror == 87:
                return 0
            raise OSError("Windows calibration member could not be opened") from error
        try:
            if not win32job.IsProcessInJob(handle, self.job):
                return 0
            if pid == self.interpreter[0] and self.interpreter[1] == creation_time(
                int(handle)
            ):
                return 0
            return win32process.GetProcessMemoryInfo(handle)["WorkingSetSize"]
        except pywintypes.error as error:
            if win32event.WaitForSingleObject(handle, 0) != win32event.WAIT_OBJECT_0:
                raise OSError(
                    "Windows calibration member working set unavailable"
                ) from error
        finally:
            handle.Close()
        return 0

    def force_stop(self):
        try:
            self.signal(KILL_SIGNAL)
        except pywintypes.error as error:
            raise OSError("Windows calibration job could not be stopped") from error
        deadline = time.monotonic() + 5
        while self.poll() is None or self.has_members():
            if time.monotonic() >= deadline:
                raise OSError("Windows calibration job members did not terminate")
            time.sleep(0.01)
        return [
            {
                "pid": self.pid,
                "process_start": self.identity,
                "job_object": self.job_name,
                "stopped": True,
            }
        ]

    def retire(self):
        try:
            if self.poll() is None or self.has_members():
                return self.force_stop()
            return []
        finally:
            self.close()
