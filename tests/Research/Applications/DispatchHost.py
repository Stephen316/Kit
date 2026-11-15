import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from tests.Research.Applications.DispatchWait import DispatchWait

# isolated application fixtures need a stable checkout anchor when their working directories change
KRepoRoot = FilePath(__file__).resolve().parents[3]


# application transport checks need real client and host processes around one private endpoint
class DispatchHost(DispatchWait):

    # each transport case needs its own endpoint and installation to prevent cross case interference
    def __init__(self, RootPath: FilePath) -> None:
        super().__init__(RootPath / "Endpoint")
        self.RootPath = RootPath
        self.Endpoint.mkdir(mode=0o700)
        self.ConfigFile = RootPath / "Installation.json"
        Revision = Subprocess.run(
            ["git", "-C", str(KRepoRoot), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        ).stdout.strip()
        _ = self.ConfigFile.write_text(
            JsonCodec.dumps(
                {
                    "version": 1,
                    "installation": "fixture:installation",
                    "application": "fusion",
                    "endpoint": str(self.Endpoint),
                    "source_root": str(KRepoRoot),
                    "source_revision": Revision,
                }
            ),
            encoding="utf-8",
        )
        self.Command = [
            System.executable,
            str(KRepoRoot / "re/automation/ApplicationWorkers/ProtocolFixture.py"),
        ]

    # host startup uses the executable fixture so checks exercise operating system process ownership
    def StartHost(self, Operation: str = "host") -> "Subprocess.Popen[str]":
        return Subprocess.Popen(
            self.Command + [Operation, "--installation", str(self.ConfigFile)],
            stdout=Subprocess.PIPE,
            stderr=Subprocess.PIPE,
            text=True,
        )

    # client startup remains independent so transport races reflect real concurrent requesters
    def StartClient(
        self, ModeValue: str = "echo", Seconds: int = 15
    ) -> "Subprocess.Popen[str]":
        return Subprocess.Popen(
            self.Command
            + [
                "client",
                "--installation",
                str(self.ConfigFile),
                "--mode",
                ModeValue,
                "--seconds",
                str(Seconds),
            ],
            stdout=Subprocess.PIPE,
            stderr=Subprocess.PIPE,
            text=True,
        )
