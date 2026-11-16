from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath


# hosted command failures must follow stderr redirection established after the entry point was imported
def CheckRedirect(TmpPath: FilePath) -> None:
    Result = RunProcess(
        (
            KPythonPath,
            "-I",
            "-c",
            """import io
import json
import sys
from contextlib import redirect_stderr
from convert.Commands.MainEntry import MainEntry
sys.argv[:] = ["convert", "research", "--root", ".", "controller", "--help"]
# the host must receive diagnostics in the stream it installs after importing the command
KErrorStream = io.StringIO()
with redirect_stderr(KErrorStream):
    # the process transports the returned status alongside the captured structured diagnostic
    KResult = MainEntry()
print(json.dumps({"code": KResult, "error": json.loads(KErrorStream.getvalue())}))
""",
        ),
        cwd=TmpPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Result.returncode == 0, Result.stderr
    assert Result.stderr == ""
    assert LoadJson(Result.stdout) == {
        "code": 1,
        "error": {
            "error": "ValueError",
            "message": "Run research with kit or python -m KitCli",
        },
    }
