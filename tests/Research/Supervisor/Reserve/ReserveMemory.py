import json as JsonCodec
import os as OsLayer
import select as SelectLayer
import sys as System
from pathlib import Path as FilePath

# the fixture and child must agree on the units in the live linux memory measurements
KMemoryMib = 1048576

# a small allocation should cross the configured reserve while leaving real memory available
KAllocMib = 384


# the allocation witness only belongs on the explicitly selected disposable linux runner
def IsHosted() -> bool:
    return (
        System.platform == "linux"
        and OsLayer.environ.get("GITHUB_ACTIONS") == "true"
        and OsLayer.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"
        and OsLayer.environ.get("KIT_RESERVE_WITNESS") == "1"
    )


# unit validation keeps independent kernel memory readings comparable with supervisor records
def ReadMemory(PathText: str, FieldName: str) -> int:
    for LineText in FilePath(PathText).read_text(encoding="ascii").splitlines():
        Fields = LineText.split()
        if len(Fields) == 3 and Fields[0] == FieldName and Fields[2] == "kB":
            return int(Fields[1]) * 1024 // KMemoryMib
    raise ValueError(f"Linux field {FieldName} is unavailable")


# host free memory alone cannot protect a process group with a smaller kernel limit
def CheckGroupRoom() -> None:
    RootPath = FilePath("/sys/fs/cgroup").resolve(strict=True)
    Membership = FilePath("/proc/self/cgroup").read_text(encoding="ascii").splitlines()
    if len(Membership) != 1 or not Membership[0].startswith("0::/"):
        raise ValueError("a unified cgroup membership is required")
    ScopePath = (RootPath / Membership[0][4:]).resolve(strict=True)
    if not ScopePath.is_relative_to(RootPath):
        raise ValueError("the unified cgroup is outside the cgroup mount")
    Controllers = (RootPath / "cgroup.controllers").read_text(encoding="ascii").split()
    if "memory" not in Controllers:
        raise ValueError("the memory cgroup controller is unavailable")
    for GroupPath in (ScopePath, *ScopePath.parents):
        if not GroupPath.is_relative_to(RootPath):
            break
        if GroupPath == RootPath:
            continue
        Maximum = (GroupPath / "memory.max").read_text(encoding="ascii").strip()
        Threshold = (GroupPath / "memory.high").read_text(encoding="ascii").strip()
        Current = int((GroupPath / "memory.current").read_text(encoding="ascii"))
        for Limit in (Maximum, Threshold):
            if (
                Limit != "max"
                and int(Limit) - Current < (2048 + KAllocMib) * KMemoryMib
            ):
                raise ValueError("insufficient cgroup memory for a bounded allocation")


# the child must recheck host and cgroup headroom immediately before allocating pages
def RequireRoom() -> int:
    if not IsHosted():
        raise ValueError("the hosted Linux reserve witness is disabled")
    if System.platform == "linux" and len(OsLayer.sched_getaffinity(0)) < 4:
        raise ValueError("four eligible logical CPUs are required")
    Available = ReadMemory("/proc/meminfo", "MemAvailable:")
    if Available < 8192 + KAllocMib:
        raise ValueError("insufficient host memory for a bounded allocation")
    CheckGroupRoom()
    return Available


# one owned child holds real resident pages until the supervisor has observed the crossing
def HoldAllocation() -> None:
    if System.platform != "linux":
        raise ValueError("the reserve witness requires Linux")
    import resource as ResourceLimits

    ReserveMib = int(System.argv[1])
    Before = RequireRoom()
    if not 64 <= Before - ReserveMib <= KAllocMib - 64:
        raise ValueError("host memory moved outside the bounded crossing window")
    LimitBytes = 512 * KMemoryMib
    ResourceLimits.setrlimit(ResourceLimits.RLIMIT_AS, (LimitBytes, LimitBytes))
    Buffer = bytearray(KAllocMib * KMemoryMib)
    PageSize = OsLayer.sysconf("SC_PAGE_SIZE")
    PageCount = (len(Buffer) + PageSize - 1) // PageSize
    Buffer[::PageSize] = b"x" * PageCount
    Loaded = ReadMemory("/proc/meminfo", "MemAvailable:")
    Resident = ReadMemory("/proc/self/status", "VmRSS:")
    if Loaded < 8192 or Resident < KAllocMib:
        raise ValueError(
            "the allocated pages or safe ambient headroom were not observed"
        )
    print(
        JsonCodec.dumps(
            {
                "pid": OsLayer.getpid(),
                "mib": len(Buffer) // KMemoryMib,
                "before_mib": Before,
                "loaded_mib": Loaded,
                "rss_mib": Resident,
            }
        ),
        flush=True,
    )
    Ready, _, _ = SelectLayer.select([System.stdin], [], [], 28)
    if not Ready or System.stdin.readline() != "release\n":
        raise ValueError("reserve witness allocation was not released within its limit")
    Buffer.clear()


if __name__ == "__main__":
    HoldAllocation()
