# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
from contextlib import ExitStack, contextmanager
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from LogCapture import LogCapture
from Records import canonical
from VerifySolidWorksBossWitness import (
    CheckControl,
    CheckFields,
    CheckMeasure,
    CheckOperation,
    CheckProcess,
    DriveAxes,
    RequireProof,
    VerifyPlan,
    VerifyWitness,
)

# source paths resolve against the exact research checkout before native launch
CheckoutRoot = Path(__file__).resolve().parents[2]

# the companion compiler consumes only the approved historical partial sources
AuthoringRoot = Path("re/automation/PairedCaptures/SolidWorksAuthoring")

# a fixed hook leaves the existing queued readback workflow unchanged
LauncherPath = AuthoringRoot / "RunBossWitness.ps1"

# only exact committed implementation bytes may enter the owner collection
PinnedSources = (
    Path("re/automation/RunSolidWorksBossWitness.py"),
    Path("re/automation/VerifySolidWorksBossWitness.py"),
    Path("re/automation/Records.py"),
    Path("re/automation/WindowsProcess.py"),
    Path("re/automation/WindowsApi.py"),
    Path("re/automation/WindowsJobMembers.py"),
    Path("re/automation/LogCapture.py"),
    Path("re/automation/ApplicationWorkers/ApplicationProtocol.py"),
    Path("re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py"),
    Path("re/automation/ApplicationWorkers/WindowsIdentity.py"),
    Path("re/automation/ApplicationWorkers/WindowsRecords.py"),
    LauncherPath,
    AuthoringRoot / "BossWitnessReadback.cs",
    AuthoringRoot / "P04Readback.cs",
    AuthoringRoot / "P02Readback.cs",
)


# licensed helpers are imported only on the owner windows host
if sys.platform == "win32":
    sys.path.insert(1, str(Path(__file__).resolve().parent / "ApplicationWorkers"))

    import win32event

    from ApplicationProtocol import (
        MAX_BYTES,
        directory,
        file_bytes,
        record,
        sha256,
        windows_git,
        write_new,
        write_record,
    )
    from ApplicationWorkers.WindowsIdentity import GET_PROCESS_TIMES, peer_matches
    from SolidWorksReadbackWorker import native_identity, registered_executable
    from WindowsJobMembers import has_job_members
    from WindowsProcess import WindowsProcess


# the installed helper bundle is pinned independently of the fixture generation commit
def SourcePins(Revision):
    RequireProof(
        re.fullmatch(r"[0-9a-f]{40}", Revision), "expected a full collector commit"
    )
    GitCommand = [windows_git(), "--no-replace-objects", "-C", str(CheckoutRoot)]
    Head = subprocess.check_output(
        [*GitCommand, "rev-parse", "--verify", "HEAD^{commit}"], timeout=15
    ).strip()
    RequireProof(
        Head == Revision.encode("ascii"), "collector checkout differs from its revision"
    )
    Sources = {}
    for Relative in PinnedSources:
        PathText = Relative.as_posix()
        Source = file_bytes(CheckoutRoot / Relative)
        Committed = subprocess.check_output(
            [*GitCommand, "show", f"{Revision}:{PathText}"], timeout=15
        )
        RequireProof(Source == Committed, f"collector source changed: {PathText}")
        Sources[PathText] = sha256(Source)
    return Sources


# the same oracle lease serializes this standalone capture with existing research hosts
@contextmanager
def OracleLease():
    Mutex = win32event.CreateMutex(None, False, r"Local\KitResearchControllerOracle")
    try:
        Acquired = win32event.WaitForSingleObject(Mutex, 0)
        RequireProof(Acquired in (0, 128), "the shared application oracle is busy")
        try:
            yield
        finally:
            win32event.ReleaseMutex(Mutex)
    finally:
        Mutex.Close()


# phase argv binds each collector to its measured private inputs
def PhaseCommand(
    Executable, Witness=None, PhaseName=None, PlanHash=None, InputHash=None
):
    PowerShell = (
        Path(os.environ["SystemRoot"])
        / "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    BaseCommand = [
        str(PowerShell),
        "-NoProfile",
        "-NonInteractive",
        "-STA",
        "-File",
        str(CheckoutRoot / LauncherPath),
        "-ExecutablePath",
        str(Executable),
    ]
    if Witness is None:
        return [*BaseCommand, "-CompileOnly"]
    RequireProof(PhaseName in ("edit", "reopen"), "unexpected licensed witness phase")
    return [
        *BaseCommand,
        "-PhaseName",
        PhaseName,
        "-WitnessDirectory",
        str(Witness),
        "-PlanSha256",
        PlanHash,
        "-InputSha256",
        InputHash,
    ]


# scripts cannot inherit profile module resolution from an unrelated powershell session
def PhaseEnv():
    return {
        Key: Value
        for Key, Value in os.environ.items()
        if Key.casefold() != "psmodulepath"
    }


# check again immediately before direct launch to preserve any unrelated cad session
def CheckStopped():
    TaskList = Path(os.environ["SystemRoot"]) / "System32/tasklist.exe"
    Running = subprocess.check_output(
        [str(TaskList), "/FI", "IMAGENAME eq SLDWORKS.exe", "/FO", "CSV", "/NH"],
        timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    RequireProof(
        not any(
            Line.lower().startswith(b'"sldworks.exe",') for Line in Running.splitlines()
        ),
        "a preexisting SOLIDWORKS process is not owned by this witness",
    )


# application input copies must be exclusive and match their retained digest
def CopyEvidence(Source, Destination, Expected):
    Content = file_bytes(Source, MAX_BYTES)
    RequireProof(
        Content and sha256(Content) == Expected,
        f"private input pin differs: {Source.name}",
    )
    write_new(Destination, Content)


# a fresh private output keeps the generated input and prior receipts intact
def PrepareOutput(Witness, Output, Plan, PlanHash):
    Witness = directory(Witness)
    BasePath = directory(Output.parent)
    Output = BasePath / Output.name
    RequireProof(
        Output != CheckoutRoot and CheckoutRoot not in Output.parents,
        "choose private output outside the checkout",
    )
    Output.mkdir(mode=0o700, exist_ok=False)
    for Name, Expected in (
        ("Plan.json", PlanHash),
        ("Generation.json", Plan["generation_sha256"]),
        ("Candidate.SLDPRT", Plan["candidate_sha256"]),
        ("Control.SLDPRT", Plan["control"]["sha256"]),
    ):
        CopyEvidence(Witness / Name, Output / Name, Expected)
    return Output


# readiness authorizes only the already held collector for this phase
def CheckReady(Ready, PhaseName, PlanHash, InputHash, Collector):
    Expected = {
        "phase": PhaseName,
        "plan_sha256": PlanHash,
        "input_sha256": InputHash,
        "collector": {
            "pid": Collector.pid,
            "created": int(Collector.identity.split(":")[1]),
        },
    }
    RequireProof(
        canonical(Ready) == canonical(Expected),
        "collector readiness differs from the exact phase",
    )


# keep the bounded diagnostic channels draining while the collector is active
def AwaitCollector(Collector, Streams, Deadline, ReadyPath=None):
    while time.monotonic() < Deadline:
        for Capture in Streams:
            Capture.drain()
        Status = Collector.poll()
        if ReadyPath is None and Status is not None:
            RequireProof(Status == 0, "native witness collector failed")
            return None
        if ReadyPath is not None:
            RequireProof(Status is None, "collector exited before native readiness")
            try:
                return record(ReadyPath)
            except FileNotFoundError:
                pass
        time.sleep(0.05)
    raise TimeoutError("native witness phase exceeded its deadline")


# terminating only a newly created job can never target the quarantined application
def CloseOwned(Worker):
    try:
        if Worker.poll() is None or has_job_members(Worker.job):
            Worker.signal(9)
            Worker.wait(timeout=5)
            Worker.finish()
    finally:
        Worker.close()


# one direct process and one collector are retained before any native request is issued
def LaunchPhase(Output, PhaseName, PlanHash, InputHash, Executable, Timeout):
    PhasePath = Output / PhaseName
    Deadline = time.monotonic() + Timeout
    with ExitStack() as Cleanup:
        Streams = []
        for Name in ("stdout", "stderr"):
            Capture = LogCapture(PhasePath / f"{Name}.log", 1024 * 1024)
            Cleanup.callback(Capture.close)
            Streams.append(Capture)
        Environment = PhaseEnv()
        Collector = WindowsProcess(
            PhaseCommand(Executable, Output, PhaseName, PlanHash, InputHash),
            Output,
            Environment,
            Streams[0].writer,
            Streams[1].writer,
        )
        Cleanup.callback(CloseOwned, Collector)
        for Capture in Streams:
            Capture.close_writer()
        Ready = AwaitCollector(Collector, Streams, Deadline, PhasePath / "Ready.json")
        CheckReady(Ready, PhaseName, PlanHash, InputHash, Collector)
        CheckStopped()
        RequireProof(
            time.monotonic() < Deadline and Collector.poll() is None,
            "collector expired before native launch",
        )
        NullOut = Cleanup.enter_context(open(os.devnull, "wb"))
        NullErr = Cleanup.enter_context(open(os.devnull, "wb"))
        Native = WindowsProcess(
            [str(Executable)],
            Executable.parent,
            Environment,
            NullOut.fileno(),
            NullErr.fileno(),
        )
        Cleanup.callback(CloseOwned, Native)
        Identity = native_identity(Native.handle)
        RequireProof(
            Identity["pid"] == Native.pid
            and Identity["created"] == Native.identity
            and Path(Identity["image"]) == Executable
            and peer_matches(Native.pid, Native.identity),
            "the held SOLIDWORKS process differs from its registered owner and image",
        )
        WitnessPeer = {
            "pid": Native.pid,
            "created": int(Native.identity.split(":")[1]),
            "session": Identity["session"],
            "job": Native.job_name,
        }
        Launch = {**Ready, "native": WitnessPeer}
        LaunchPath = PhasePath / "Launch.json"
        write_record(LaunchPath, Launch)
        LaunchHash = sha256(file_bytes(LaunchPath))
        AwaitCollector(Collector, Streams, Deadline)
        Remaining = Deadline - time.monotonic()
        RequireProof(
            Remaining > 0 and Native.wait(timeout=Remaining) == 0,
            "owned SOLIDWORKS did not exit normally",
        )
        RequireProof(
            not has_job_members(Native.job) and not has_job_members(Collector.job),
            "owned processes did not drain naturally",
        )
        Finished = ExitTime(Native.handle)
        RequireProof(
            sha256(file_bytes(LaunchPath)) == LaunchHash,
            "the held launch record changed",
        )
        Raw = record(PhasePath / "Raw.json")
        return Raw, WitnessPeer, Finished, LaunchHash


# native exit time comes from the same retained kernel handle as the created identity
def ExitTime(Handle):
    Times = [wintypes.FILETIME() for _ in range(4)]
    if not GET_PROCESS_TIMES(Handle, *[ctypes.byref(Clock) for Clock in Times]):
        raise ctypes.WinError(ctypes.get_last_error())
    Closed = Times[1]
    return (Closed.dwHighDateTime << 32) | Closed.dwLowDateTime


# validate each completed raw phase before it can supply a successor or final report
def PhaseReceipt(
    Raw,
    Peer,
    Finished,
    LaunchHash,
    PhaseName,
    Plan,
    PlanHash,
    InputHash,
    OutputHash,
    Previous,
):
    CheckFields(
        Raw,
        "launch_sha256 input_sha256 output_sha256 open read_only save controls measurements",
    )
    RequireProof(
        Raw["launch_sha256"] == LaunchHash
        and Raw["input_sha256"] == InputHash
        and Raw["output_sha256"] == OutputHash
        and Raw["read_only"] is (PhaseName == "reopen"),
        "collector evidence differs from the measured archive custody",
    )
    Receipt = {
        Key: Raw[Key]
        for Key in ("open", "read_only", "save", "controls", "measurements")
    }
    Receipt.update(
        schema=1,
        scope=Plan["scope"],
        phase=PhaseName,
        status="observed",
        plan_sha256=PlanHash,
        prior_sha256=Previous,
        build=Plan["build"],
        input_sha256=InputHash,
        output_sha256=OutputHash,
        owner={
            "pid": Peer["pid"],
            "created": Peer["created"],
            "session": Peer["session"],
            "image_sha256": Plan["image_sha256"],
            "initial_documents": 0,
            "verified": True,
        },
        exit={
            "pid": Peer["pid"],
            "created": Peer["created"],
            "finished": Finished,
            "exit_code": 0,
            "drained": True,
        },
    )
    CheckOperation(Receipt["open"])
    CheckProcess(Receipt, Plan)
    CheckFields(Receipt["controls"], "before after")
    for Control in Receipt["controls"].values():
        CheckControl(Control, Plan["control"])
    CheckRows(Receipt, PhaseName, Plan)
    return Receipt


# the restored edit sequence is checked before another licensed process can start
def CheckRows(Receipt, PhaseName, Plan):
    Shapes = Plan["shapes"]
    Baseline = Shapes["baseline"]
    if PhaseName == "edit":
        CheckOperation(Receipt["save"])
        Expected = [("baseline", Baseline)]
        for Axis in DriveAxes:
            Expected.extend(
                ((f"{Axis}_edited", Shapes[Axis]), (f"{Axis}_restored", Baseline))
            )
    else:
        RequireProof(Receipt["save"] is None, "read only reopen returned a save")
        Expected = [("before_rebuild", Baseline), ("after_rebuild", Baseline)]
    Rows = Receipt["measurements"]
    RequireProof(
        isinstance(Rows, list) and len(Rows) == len(Expected),
        "native observation sequence is incomplete",
    )
    for Observed, (Stage, Shape) in zip(Rows, Expected, strict=True):
        CheckMeasure(Observed, Stage, Shape, Plan)


# a phase cannot publish until the file observed by its collector has been rehashed
def RunPhase(
    Output, PhaseName, Plan, PlanHash, InputHash, Executable, Timeout, Previous=None
):
    PhasePath = Output / PhaseName
    PhasePath.mkdir(mode=0o700, exist_ok=False)
    Archive = Output / "Restored.SLDPRT"
    Edit = PhaseName == "edit"
    if Edit:
        Archive = PhasePath / "Scratch.SLDPRT"
        CopyEvidence(Output / "Candidate.SLDPRT", Archive, InputHash)
    Raw, Peer, Finished, LaunchHash = LaunchPhase(
        Output, PhaseName, PlanHash, InputHash, Executable, Timeout
    )
    OutputHash = sha256(file_bytes(Archive, MAX_BYTES))
    RequireProof(
        Edit or OutputHash == InputHash, "read only reopen modified the saved archive"
    )
    Receipt = PhaseReceipt(
        Raw,
        Peer,
        Finished,
        LaunchHash,
        PhaseName,
        Plan,
        PlanHash,
        InputHash,
        OutputHash,
        Previous,
    )
    if Edit:
        CopyEvidence(Archive, Output / "Restored.SLDPRT", OutputHash)
    ReceiptPath = Output / f"{PhaseName.title()}.json"
    write_record(ReceiptPath, Receipt)
    return sha256(file_bytes(ReceiptPath)), OutputHash


# the compile and execution receipts bind the exact installed interop files
def InstallPins(Executable):
    InteropRoot = Executable.parent / "api/redist"
    return {
        FilePath.name: sha256(file_bytes(FilePath, MAX_BYTES))
        for FilePath in (
            Executable,
            InteropRoot / "SolidWorks.Interop.sldworks.dll",
            InteropRoot / "SolidWorks.Interop.swconst.dll",
        )
    }


# preserve diagnostics under a new private root if any native phase refuses
def CollectWitness(Arguments, Sources, Executable):
    Plan = VerifyPlan(Arguments.witness, Arguments.plan_sha256)
    Installation = InstallPins(Executable)
    RequireProof(
        Plan["image_sha256"] == Installation[Executable.name],
        "installed SOLIDWORKS image differs from plan",
    )
    with OracleLease():
        CheckStopped()
        Output = PrepareOutput(
            Arguments.witness, Arguments.output, Plan, Arguments.plan_sha256
        )
        try:
            write_record(
                Output / "Collector.json",
                {
                    "revision": Arguments.collector_revision,
                    "sources": Sources,
                    "installation": Installation,
                },
            )
            EditHash, SavedHash = RunPhase(
                Output,
                "edit",
                Plan,
                Arguments.plan_sha256,
                Plan["candidate_sha256"],
                Executable,
                Arguments.timeout_seconds,
            )
            ReopenHash, _ = RunPhase(
                Output,
                "reopen",
                Plan,
                Arguments.plan_sha256,
                SavedHash,
                Executable,
                Arguments.timeout_seconds,
                EditHash,
            )
            RequireProof(
                SourcePins(Arguments.collector_revision) == Sources,
                "collector sources changed during observation",
            )
            RequireProof(
                InstallPins(Executable) == Installation,
                "licensed installation bytes changed during observation",
            )
            return VerifyWitness(Output, Arguments.plan_sha256, EditHash, ReopenHash)
        except Exception as Problem:
            write_record(
                Output / "Failure.json",
                {"error": type(Problem).__name__, "reason": str(Problem)[:4096]},
            )
            raise


# compilation can verify the real installed interops while avoiding native phase dispatch
def MainRun():
    Parser = argparse.ArgumentParser(
        description="Collect a bounded SOLIDWORKS rectangular Boss witness"
    )
    Parser.add_argument("--collector-revision", required=True)
    Parser.add_argument("--compile-only", action="store_true")
    Parser.add_argument("--witness", type=Path)
    Parser.add_argument("--plan-sha256")
    Parser.add_argument("--output", type=Path)
    Parser.add_argument("--timeout-seconds", type=int, default=300)
    Arguments = Parser.parse_args()
    NativeOptions = (Arguments.witness, Arguments.plan_sha256, Arguments.output)
    if Arguments.compile_only and any(NativeOptions):
        Parser.error("compile only takes no native witness arguments")
    if not Arguments.compile_only and not all(NativeOptions):
        Parser.error(
            "provide the private witness, exact plan digest and a new output directory"
        )
    if not 1 <= Arguments.timeout_seconds <= 3600:
        Parser.error("phase timeout must be between 1 and 3600 seconds")
    if sys.platform != "win32":
        Parser.error("the licensed SOLIDWORKS companion requires Windows")
    try:
        Sources = SourcePins(Arguments.collector_revision)
        Executable = registered_executable()
        if Arguments.compile_only:
            subprocess.run(
                PhaseCommand(Executable), check=True, env=PhaseEnv(), timeout=120
            )
        else:
            print(canonical(CollectWitness(Arguments, Sources, Executable)))
    except Exception as Problem:
        Parser.exit(1, f"witness collection refused: {Problem}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
