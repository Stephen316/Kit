import sys as System


def BindChild(
    LauncherPid: int, CallerPid: int, Observation: dict[str, int], JobName: str
) -> list[int]:
    if System.platform != "win32":
        raise OSError("Windows child binding requires a Windows host")
    import win32api as WindowsApi
    import win32con as WindowsFlags
    import win32job as WindowsJobs

    ApplicationPid = Observation["application_pid"]
    ParentPid = Observation["parent_pid"]
    assert Observation["caller_pid"] == CallerPid, Observation
    assert (ApplicationPid == LauncherPid and ParentPid == CallerPid) or (
        ApplicationPid != LauncherPid and ParentPid == LauncherPid
    ), {"launcher": LauncherPid, "caller": CallerPid, "observation": Observation}
    ProcessIds = sorted({CallerPid, LauncherPid, ApplicationPid})
    JobHandle = WindowsJobs.OpenJobObject(WindowsJobs.JOB_OBJECT_QUERY, False, JobName)
    try:
        for ProcessId in ProcessIds:
            ProcessHandle = WindowsApi.OpenProcess(
                WindowsFlags.PROCESS_QUERY_LIMITED_INFORMATION, False, ProcessId
            )
            try:
                assert WindowsJobs.IsProcessInJob(ProcessHandle, JobHandle), ProcessId
            finally:
                ProcessHandle.Close()
    finally:
        JobHandle.Close()
    return ProcessIds
