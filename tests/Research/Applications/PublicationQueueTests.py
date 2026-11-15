import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.PublicationHost import KFixturePath


# large repeated transport exchanges must preserve complete records without conferring native qualification
def CheckRecordFlow() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = DispatchHost(FilePath(TempPath).resolve())
        Harness.Command = [System.executable, str(KFixturePath)]
        Server = Harness.StartHost()
        try:
            _ = Harness.WaitFile("ready.json")
            ResultInfo = Subprocess.run(
                Harness.Command
                + ["exchange", "--installation", str(Harness.ConfigFile)],
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
            assert ResultInfo.returncode == 0, ResultInfo.stderr
            Result = JsonCodec.loads(ResultInfo.stdout)
            assert Result["round_trips"] == 32
            assert Result["payload_bytes"] > 900000
            assert Result["native_qualified"] is False
            assert not list(
                Harness.Endpoint.rglob(".*.????????????????????????????????")
            )
        finally:
            Server.terminate()
            _ = Server.communicate(timeout=15)
