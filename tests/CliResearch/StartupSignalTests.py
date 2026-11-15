from pathlib import Path as FilePath
from signal import Signals
from subprocess import PIPE as KPipe, Popen as StartProcess
from sys import executable as KPythonPath, platform as KPlatform
from time import sleep as WaitSeconds

from pytest import mark as TestMark

from tests.CliResearch.PrepareSignal import PrepareSignal
from tests.CliResearch.PrepareStartup import PrepareStartup


# cancellation during the real spawn handoff must reach the child after ownership becomes available
@TestMark.skipif(KPlatform == "win32", reason="POSIX research startup ownership")
@TestMark.parametrize("SignalNames", (("SIGTERM",), ("SIGTSTP", "SIGCONT", "SIGTERM")))
def CheckStartup(SignalNames: tuple[str, ...], TmpPath: FilePath) -> None:
    RootPath = PrepareSignal(TmpPath)
    BootstrapPath = PrepareStartup(TmpPath)
    ReadyPath = TmpPath / "Ready"
    DonePath = TmpPath / "Done"
    SpawnedPath = TmpPath / "Spawned"
    ReleasePath = TmpPath / "Release"
    with StartProcess(
        (
            KPythonPath,
            "-I",
            str(BootstrapPath),
            str(RootPath),
            str(ReadyPath),
            str(DonePath),
            str(SpawnedPath),
            str(ReleasePath),
        ),
        cwd=TmpPath,
        stdout=KPipe,
        stderr=KPipe,
        text=True,
    ) as Launcher:
        try:
            for _ in range(3000):
                if (
                    ReadyPath.exists() and SpawnedPath.exists()
                ) or Launcher.poll() is not None:
                    break
                WaitSeconds(0.01)
            assert ReadyPath.read_text() == "selected research sdk"
            assert SpawnedPath.read_text() == (TmpPath / "ChildPid").read_text()
            for SignalName in SignalNames:
                Launcher.send_signal(Signals[SignalName])
                WaitSeconds(0.05)
            _ = ReleasePath.write_text("continue")
            _, ErrorText = Launcher.communicate(timeout=60)
            assert Launcher.returncode == 37, ErrorText
            assert DonePath.read_text() == "cleaned"
        finally:
            _ = ReleasePath.write_text("continue")
            if Launcher.poll() is None:
                Launcher.send_signal(Signals["SIGCONT"])
                Launcher.terminate()
            _ = Launcher.wait(timeout=30)
