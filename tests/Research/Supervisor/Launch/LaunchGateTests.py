import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.Launch.LaunchHost import (
    StartGateHost,
    WaitBootstrap,
    WaitGateStop,
)
from tests.Research.Supervisor.StopGroup import StopGroup
from tests.Research.SupervisorClient import IsGoneByTimeout


def CheckGateEof() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Launcher = StartGateHost(RootPath)
        BootstrapId = None
        try:
            BootstrapId = WaitBootstrap(RootPath)
            Launcher.kill()
            _ = Launcher.communicate(timeout=15)
            assert IsGoneByTimeout(BootstrapId)
            assert not (RootPath / "worker-entered.json").exists()
            assert not (RootPath / "session.json").exists()
        finally:
            if Launcher.poll() is None:
                Launcher.kill()
            _ = Launcher.communicate(timeout=15)
            StopGroup(BootstrapId, None)


def CheckGateWait() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Launcher = StartGateHost(RootPath)
        BootstrapId = None
        try:
            BootstrapId = WaitBootstrap(RootPath)
            WaitGateStop(BootstrapId)
            assert Launcher.poll() is None
            OutputText, ErrorText = Launcher.communicate(input="", timeout=15)
            assert Launcher.returncode == 0, OutputText + ErrorText
            Reaped = JsonCodec.loads(
                (RootPath / "reaped.json").read_text(encoding="utf-8")
            )
            assert Reaped["returncode"] == 124
            assert not (RootPath / "worker-entered.json").exists()
        finally:
            if Launcher.poll() is None:
                Launcher.kill()
            _ = Launcher.communicate(timeout=15)
            StopGroup(BootstrapId, None)
