import json as JsonCodec
import select as SelectLayer
import subprocess as Subprocess
import sys as System
import time as TimeClock
from contextlib import contextmanager as ContextManager
from pathlib import Path as FilePath
from typing import Iterator, cast as CastValue

from tests.Research.Supervisor.AdaptiveHost import MakeAdaptive
from tests.Research.SupervisorClient import FixtureJob, SessionHost


# both workers must stay alive across the reserve crossing so the capacity clamp stays at two
def MakeReserveHost(RootPath: FilePath, ReserveMib: int) -> SessionHost:
    Harness = MakeAdaptive(RootPath, PoolLimit=4)
    Configuration = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
    Configuration["reserved_memory_mib"] = ReserveMib
    _ = Harness.ConfigFile.write_text(JsonCodec.dumps(Configuration), encoding="utf-8")
    RegistryFile = RootPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryFile.read_text(encoding="utf-8"))
    Registry["runners"]["fixture.decode"]["initial_peak_memory_mib"] = 32
    _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
    Harness.SubmitJobs(
        [
            FixtureJob(
                JobName,
                "fixture.decode",
                max_attempts=1,
                lease_seconds=25,
                timeout_seconds=65,
                options={"hold_seconds": 42},
            )
            for JobName in ("reserve:first", "reserve:second")
        ]
    )
    return Harness


# a new measured decision avoids confusing a retained old status with a sustained observation
def WaitReserve(
    Harness: SessionHost, Active: int, Expected: int, After: float = 0
) -> tuple[float, int]:
    Until = TimeClock.monotonic() + 12
    Previous: dict[str, object] = {}
    while TimeClock.monotonic() < Until:
        DecodePool = JsonCodec.loads(Harness.RunCli("status", Timeout=5))["pools"][
            "decode"
        ]
        Current = CastValue(dict[str, object], DecodePool["capacity"]["decision"] or {})
        Previous = Current
        Sample = Current.get("host_measured_at")
        Revision = Current.get("adaptive_revision")
        if (
            len(DecodePool["running"]) == 2
            and Current.get("active_limit") == Active
            and isinstance(Sample, (int, float))
            and Sample > After
            and isinstance(Revision, int)
            and Current.get("calculated_capacity") == Expected
        ):
            return Sample, Revision
        TimeClock.sleep(0.15)
    raise AssertionError(
        f"reserve decision did not reach {Active}/{Expected}: {Previous}"
    )


# only the allocator we launched may hold memory and it must be released on every exit path
@ContextManager
def ReserveChild(ReserveMib: int) -> Iterator[dict[str, int]]:
    with Subprocess.Popen(
        [
            System.executable,
            str(FilePath(__file__).with_name("ReserveMemory.py")),
            str(ReserveMib),
        ],
        stdin=Subprocess.PIPE,
        stdout=Subprocess.PIPE,
        stderr=Subprocess.PIPE,
        text=True,
    ) as Child:
        try:
            assert Child.stdout is not None
            Readable, _, _ = SelectLayer.select([Child.stdout], [], [], 8)
            assert Readable, "reserve allocator did not acknowledge its owned pages"
            Receipt: dict[str, int] = JsonCodec.loads(Child.stdout.readline())
            assert Receipt["pid"] == Child.pid and Child.poll() is None
            yield Receipt
        finally:
            try:
                _, ErrorText = Child.communicate("release\n", timeout=5)
            except Subprocess.TimeoutExpired:
                Child.kill()
                _, ErrorText = Child.communicate(timeout=5)
                raise AssertionError(f"reserve allocator did not release: {ErrorText}")
            assert Child.returncode == 0, ErrorText
