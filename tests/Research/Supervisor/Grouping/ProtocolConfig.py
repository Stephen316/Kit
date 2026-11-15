import json as JsonCodec
import subprocess as Subprocess
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import SessionHost


# invalid group protocols must fail before the supervisor can claim production work
def RejectGroupApi(Harness: SessionHost, RootPath: FilePath, SourceText: str) -> str:
    AdapterFile = RootPath / "BrokenAdapter.py"
    _ = AdapterFile.write_text(
        "from Adapters import A03Adapter\n" + SourceText, encoding="utf-8"
    )
    ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
    ConfigInfo["controller"] = {
        "module": str(AdapterFile),
        "class": "A03Adapter",
        "options": {"store": str(RootPath / "Store")},
    }
    _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
    ResultInfo = Subprocess.run(
        Harness.Command + ["run", "--idle-seconds", "1", "--max-seconds", "10"],
        capture_output=True,
        text=True,
        check=False,
        env=Harness.Environment,
        timeout=30,
    )
    assert ResultInfo.returncode == 1, ResultInfo.stdout
    return ResultInfo.stderr
