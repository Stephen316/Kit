import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from tests.Research.Applications.DispatchWait import DispatchWait

KRepoRoot = FilePath(__file__).resolve().parents[3]


class DispatchHost(DispatchWait):
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

    def StartHost(self, Operation: str = "host") -> "Subprocess.Popen[str]":
        return Subprocess.Popen(
            self.Command + [Operation, "--installation", str(self.ConfigFile)],
            stdout=Subprocess.PIPE,
            stderr=Subprocess.PIPE,
            text=True,
        )

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
