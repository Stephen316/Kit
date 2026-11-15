from pathlib import Path as FilePath
from signal import SIGTERM, Signals
from subprocess import PIPE as KPipe, Popen as StartProcess
from sys import executable as KPythonPath, platform as KPlatform
from time import sleep as WaitSeconds

from pytest import mark as TestMark

from tests.CliResearch.PrepareSignal import PrepareSignal


# direct launcher signals must reach the selected sdk process without losing cleanup or exit status
@TestMark.skipif(KPlatform == "win32", reason="POSIX research signal propagation")
@TestMark.parametrize(
    "SignalName,HandleSignal,ExpectedCode",
    (
        ("SIGTERM", True, 37),
        ("SIGINT", True, 37),
        ("SIGHUP", True, 37),
        ("SIGQUIT", True, 37),
        ("SIGUSR1", True, 37),
        ("SIGUSR2", True, 37),
        ("SIGTERM", False, -SIGTERM),
    ),
)
def CheckSignal(
    SignalName: str, HandleSignal: bool, ExpectedCode: int, TmpPath: FilePath
) -> None:
    RootPath = PrepareSignal(TmpPath)
    ReadyPath = TmpPath / "Ready"
    DonePath = TmpPath / "Done"
    with StartProcess(
        (
            KPythonPath,
            "-I",
            "-m",
            "KitCli",
            "research",
            "--root",
            str(RootPath),
            "controller",
            str(ReadyPath),
            str(DonePath),
            "handled" if HandleSignal else "default",
        ),
        cwd=TmpPath,
        stdout=KPipe,
        stderr=KPipe,
        text=True,
    ) as Launcher:
        try:
            for _ in range(3000):
                if ReadyPath.exists() or Launcher.poll() is not None:
                    break
                WaitSeconds(0.01)
            assert ReadyPath.read_text() == "selected research sdk"
            Launcher.send_signal(Signals[SignalName])
            _, ErrorText = Launcher.communicate(timeout=60)
            assert Launcher.returncode == ExpectedCode, ErrorText
            assert DonePath.exists() is HandleSignal
            if HandleSignal:
                assert DonePath.read_text() == "cleaned"
        finally:
            if Launcher.poll() is None:
                Launcher.send_signal(Signals["SIGCONT"])
                Launcher.terminate()
            _ = Launcher.wait(timeout=30)
