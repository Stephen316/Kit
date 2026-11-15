import hashlib as HashLib
import json as JsonCodec
import plistlib as PlistCodec
import shutil as FileOps
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import KRepoRoot

# the standalone process uses the same kernel and captured handoff comparison as the owner command
KPeerCommand = """
import json
import sys
import time
from pathlib import Path
from ApplicationProtocol import identity
from FusionRestartPeer import match_peer
from MacApplicationBundle import pinned_bundle
from MacApplicationPeer import process_peer

pid = int(sys.argv[1])
host = identity(pid)
bundle = pinned_bundle(Path(sys.argv[2]).read_bytes(), '1' * 64)
when = time.time()
if sys.argv[3] == 'stale':
    when = (process_peer(pid)['started_unix_microseconds'] - 1) / 1_000_000
observed = match_peer({'host': host, 'at': when}, bundle['executable'])
del observed['executable']
print(json.dumps(observed))
"""


# the disposable executable exercises the real macos process identity without vendor software
def PrepareBundle(RootPath: FilePath) -> FilePath:
    BundlePath = RootPath / "Fixture.app"
    BinaryPath = BundlePath / "Contents/MacOS/Fixture"
    BinaryPath.parent.mkdir(parents=True)
    PlistPath = BundlePath / "Contents/Info.plist"
    _ = PlistPath.write_bytes(
        PlistCodec.dumps(
            {
                "CFBundlePackageType": "APPL",
                "CFBundleExecutable": "Fixture",
                "CFBundleIdentifier": "org.unicad.fixture",
            }
        )
    )
    Compiled = Subprocess.run(
        ["/usr/bin/clang", "-x", "c", "-o", str(BinaryPath), "-"],
        input="#include <unistd.h>\nint main(void) { for (;;) pause(); }\n",
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Compiled.returncode == 0, Compiled.stderr
    return BinaryPath


# each private profile binds the same owner configuration and pins only physical bundle files
def WriteProfile(ProfilePath: FilePath, BinaryPath: FilePath) -> None:
    BundlePath = BinaryPath.parents[2]
    PlistPath = BundlePath / "Contents/Info.plist"
    ConfigInfo = {
        "version": 1,
        "installation_sha256": "1" * 64,
        "bundle": str(BundlePath),
        "info_sha256": HashLib.sha256(PlistPath.read_bytes()).hexdigest(),
        "executable_sha256": HashLib.sha256(BinaryPath.read_bytes()).hexdigest(),
    }
    _ = ProfilePath.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")


# asserting through a separate process also exposes any native abi or bundle layout mismatch
def ReadMacPeer(
    ProcessId: int, ProfilePath: FilePath, ModeName: str = "live"
) -> Subprocess.CompletedProcess[str]:
    return Subprocess.run(
        [
            System.executable,
            "-B",
            "-c",
            KPeerCommand,
            str(ProcessId),
            str(ProfilePath),
            ModeName,
        ],
        cwd=KRepoRoot / "re/automation/ApplicationWorkers",
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )


# changed start time and a second bundle with identical bytes must not identify the accepted peer
def AssertPeer(ProcessId: int, ProfilePath: FilePath, OtherPath: FilePath) -> None:
    Observed = ReadMacPeer(ProcessId, ProfilePath)
    assert Observed.returncode == 0, Observed.stderr
    PeerInfo = JsonCodec.loads(Observed.stdout)
    assert PeerInfo["pid"] == ProcessId and PeerInfo["uid"] > 0
    assert PeerInfo["started_unix_microseconds"] > 0
    assert JsonCodec.loads(ReadMacPeer(ProcessId, ProfilePath).stdout) == PeerInfo
    Stale = ReadMacPeer(ProcessId, ProfilePath, "stale")
    assert (
        Stale.returncode != 0
        and "differs from the accepted Fusion peer" in Stale.stderr
    )
    Wrong = ReadMacPeer(ProcessId, OtherPath)
    assert (
        Wrong.returncode != 0
        and "differs from the accepted Fusion peer" in Wrong.stderr
    )


# only macos runners exercise this operating system boundary and the fixture owns its child
@TestMark.skipif(System.platform != "darwin", reason="macOS kernel process identity")
def CheckMacPeer(TmpPath: FilePath) -> None:
    RootPath = TmpPath.resolve()
    BinaryPath = PrepareBundle(RootPath)
    ProfilePath = RootPath / "Lifecycle.json"
    OtherPath = RootPath / "Other.json"
    OtherBundle = RootPath / "Other.app"
    _ = FileOps.copytree(BinaryPath.parents[2], OtherBundle)
    WriteProfile(ProfilePath, BinaryPath)
    WriteProfile(OtherPath, OtherBundle / "Contents/MacOS/Fixture")
    with Subprocess.Popen([str(BinaryPath)]) as Process:
        try:
            AssertPeer(Process.pid, ProfilePath, OtherPath)
            assert Process.poll() is None
        finally:
            if Process.poll() is None:
                Process.terminate()
            _ = Process.wait(timeout=10)
