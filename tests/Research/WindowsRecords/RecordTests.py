import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchWait import DispatchWait
from tests.Research.WindowsRecords.RecordProcess import (
    CheckBlocked,
    KFixture,
    RunRecord,
)

# file custody scenarios rely on windows sharing semantics unavailable on other platforms
KWindowsOnly = TestMark.skipif(
    System.platform != "win32", reason="Windows file handles"
)


# record identity must follow the open handle when the visible path receives different bytes
@KWindowsOnly
def CheckRewritten() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Result = RunRecord("rewritten", FilePath(TempPath).resolve())
        assert Result["size"] == len(
            b'{"version":1,"immutable":true,"rewritten":true}\n'
        )
        assert Result["path_ctime_ns"] != Result["handle_ctime_ns"]


# unsafe windows record paths must fail before immutable intake accepts their contents
@KWindowsOnly
def CheckUnsafe() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Result = RunRecord("unsafe", FilePath(TempPath).resolve())
        assert Result == {
            "hardlinks": 2,
            "reparse_paths": 2,
            "directory": True,
            "byte_limit": True,
        }


# the intake contract must detect metadata changes even when apparent content identity is stable
@KWindowsOnly
def CheckMetadata() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        Target = FilePath(str(RunRecord("prepare", RootPath)["path"]))
        assert RunRecord("metadata", Target) == {"change_time_rejected": True}


# competing writers and deletion must be refused only while the protected handle remains open
@KWindowsOnly
def CheckSharing() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve() / "Private"
        Target = FilePath(str(RunRecord("prepare", RootPath)["path"]))
        with Subprocess.Popen(
            [System.executable, str(KFixture), "hold", str(Target)],
            stdin=Subprocess.PIPE,
            stdout=Subprocess.PIPE,
            stderr=Subprocess.PIPE,
            text=True,
        ) as Reader:
            try:
                _ = DispatchWait(RootPath).WaitFile("ready")
                Result = RunRecord("mutations", Target)
                print(JsonCodec.dumps(Result, sort_keys=True), flush=True)
                CheckBlocked(Result)
                Stdout, Stderr = Reader.communicate("release\n", timeout=15)
                assert Reader.returncode == 0, Stdout + Stderr
            finally:
                if Reader.poll() is None:
                    Reader.kill()
                    _ = Reader.communicate(timeout=15)
        assert RunRecord("unlocked", Target) == dict.fromkeys(Result, True), Result
        assert (
            Target.read_bytes() == b'{"version":1,"immutable":true,"rewritten":true}\n'
        )


# the embedded worker needs bounded record and lock custody with site packages disabled
@KWindowsOnly
def CheckStdRecord(TmpPath: FilePath) -> None:
    Completed = Subprocess.run(
        [
            System.executable,
            "-I",
            "-S",
            "-c",
            """from importlib.util import find_spec
from pathlib import Path
import subprocess
import sys

assert find_spec('win32file') is None and find_spec('pywintypes') is None
sys.path.insert(0, sys.argv[1])
from ApplicationProtocol import file_bytes, owner_lock

root = Path(sys.argv[2])
data = b'protected\\r\\nrecord\\0'
target = root / 'record.json'
target.write_bytes(data)
assert file_bytes(target, len(data)) == data
try:
    file_bytes(target, len(data) - 1)
except ValueError as error:
    assert str(error) == 'application input exceeds its byte limit'
else:
    raise AssertionError('protected read accepted an out-of-bound record')
for missing in (root / 'absent.json', root / 'absent' / 'record.json'):
    try:
        file_bytes(missing)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError('protected read accepted a missing record')

lock = root / 'host.lock'
with owner_lock(lock):
    blocked = subprocess.run(
        [sys.executable, '-I', '-S', '-c',
         'import sys; sys.path.insert(0, sys.argv[1]); '
         'from ApplicationProtocol import owner_lock\\n'
         'with owner_lock(sys.argv[2]):\\n    pass',
         sys.argv[1], str(lock)],
        capture_output=True, text=True, timeout=15,
    )
    assert blocked.returncode != 0 and 'BlockingIOError' in blocked.stderr, blocked.stderr
with owner_lock(lock):
    pass
""",
            str(KFixture.parent),
            str(TmpPath),
        ],
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    assert Completed.returncode == 0, Completed.stdout + Completed.stderr
