import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.Grouping.BatchHost import MakeBatchHost
from tests.Research.Supervisor.Grouping.ProtocolConfig import RejectGroupApi


def CheckGroupApi() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        ErrorText = RejectGroupApi(Harness, RootPath, "A03Adapter.FinishGroup = None\n")
        assert "group-capable adapter must provide protocol 1" in ErrorText


def CheckGroupBool() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        ErrorText = RejectGroupApi(
            Harness, RootPath, "A03Adapter.GroupClaimsVersion = True\n"
        )
        assert "group-capable adapter must provide protocol 1" in ErrorText
