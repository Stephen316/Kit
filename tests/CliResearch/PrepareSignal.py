from pathlib import Path as FilePath


# process signal coverage needs a real selected sdk and observable research cleanup
def PrepareSignal(WorkPath: FilePath) -> FilePath:
    RootPath = WorkPath / "Checkout"
    (RootPath / ".git").mkdir(parents=True)
    SdkPath = RootPath / "src/convert"
    SdkPath.mkdir(parents=True)
    _ = (SdkPath / "__init__.py").write_text("""
# the child must identify its own selected checkout sdk
KIdentity = "selected research sdk"
""")
    ToolPath = RootPath / "re/automation/Controller.py"
    ToolPath.parent.mkdir(parents=True)
    _ = ToolPath.write_text(
        """from os import getpid
from pathlib import Path
from signal import SIGINT, SIGTERM, SIGHUP, SIGQUIT, SIGUSR1, SIGUSR2, signal
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from convert import KIdentity

# interrupted research must finish cleanup before the launcher reports completion
def Finish(Number, Frame):
    Path(sys.argv[2]).write_text("cleaned")
    raise SystemExit(37)
if sys.argv[3] == "handled":
    for Number in (SIGINT, SIGTERM, SIGHUP, SIGQUIT, SIGUSR1, SIGUSR2):
        signal(Number, Finish)
Path(sys.argv[1]).with_name("ChildPid").write_text(str(getpid()))
Path(sys.argv[1]).write_text(KIdentity)
for _ in range(3000):
    time.sleep(0.01)
raise SystemExit(38)
""",
        encoding="utf-8",
    )
    return RootPath
