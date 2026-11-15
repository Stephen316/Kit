from pathlib import Path as FilePath
from signal import SIGTERM, Signals
from subprocess import PIPE as KPipe, Popen as StartProcess
from sys import executable as KPythonPath, platform as KPlatform
from time import sleep as WaitSeconds

from pytest import mark as TestMark

from tests.CliResearch.PrepareSignal import PrepareSignal
from tests.CliResearch.WaitStopped import WaitStopped


# terminal suspension must stop both research processes and resume the child before cleanup
@TestMark.skipif(KPlatform == "win32", reason="POSIX research job control")
def CheckJobControl(TmpPath: FilePath) -> None:
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
            "handled",
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
            ChildPid = int((TmpPath / "ChildPid").read_text())
            Launcher.send_signal(Signals["SIGTSTP"])
            WaitStopped((Launcher.pid, ChildPid))
            Launcher.send_signal(Signals["SIGCONT"])
            Launcher.send_signal(SIGTERM)
            _, ErrorText = Launcher.communicate(timeout=60)
            assert Launcher.returncode == 37, ErrorText
            assert DonePath.read_text() == "cleaned"
        finally:
            if Launcher.poll() is None:
                Launcher.send_signal(Signals["SIGCONT"])
                Launcher.terminate()
            _ = Launcher.wait(timeout=30)
