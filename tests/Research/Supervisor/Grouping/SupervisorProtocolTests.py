import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.Grouping.BatchHost import MakeBatchHost
from tests.Research.Supervisor.Grouping.ProtocolConfig import RejectGroupApi


# group capability must fail closed when its runtime protocol contract is absent
def CheckGroupApi() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        ErrorText = RejectGroupApi(Harness, RootPath, "A03Adapter.FinishGroup = None\n")
        assert "group-capable adapter must provide protocol 1" in ErrorText


# a boolean capability value must not silently substitute for the versioned group protocol
def CheckGroupBool() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        ErrorText = RejectGroupApi(
            Harness, RootPath, "A03Adapter.GroupClaimsVersion = True\n"
        )
        assert "group-capable adapter must provide protocol 1" in ErrorText
