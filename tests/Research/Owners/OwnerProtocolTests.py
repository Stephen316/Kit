import tempfile as TempFiles
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Supervisor.Grouping.BatchHost import MakeBatchHost
from tests.Research.Supervisor.Grouping.ProtocolConfig import RejectGroupApi


# invalid fence advertisements must fail before the supervisor makes ownership claims
@TestMark.parametrize(
    "Declaration",
    (
        "A03Adapter.RecoveryFenceVersion = True\n",
        "A03Adapter.RecoveryFenceVersion = 2\n",
        "A03Adapter.BeginOwner = None\n",
    ),
)
def CheckFenceApi(Declaration: str) -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        Harness = MakeBatchHost(RootPath)
        ErrorText = RejectGroupApi(Harness, RootPath, Declaration)
        assert "recovery-fenced adapter" in ErrorText
