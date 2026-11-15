from os import link as LinkFile, replace as ReplaceFile
from pathlib import Path as FilePath
from stat import S_IMODE as FileMode
from tempfile import TemporaryDirectory


# inspection output needs atomic publication without overwriting sources or discarding destination permissions
def SaveDecode(Destination: FilePath, Content: str, Overwrite: bool) -> None:
    Destination = Destination.resolve()
    with TemporaryDirectory(dir=Destination.parent, prefix=".kit-") as Directory:
        TempPath = FilePath(Directory) / "Decode.json"
        _ = TempPath.write_text(Content + "\n", encoding="utf-8")
        if Overwrite:
            if Destination.exists():
                TempPath.chmod(FileMode(Destination.stat().st_mode))
            ReplaceFile(TempPath, Destination)
        else:
            LinkFile(TempPath, Destination)
