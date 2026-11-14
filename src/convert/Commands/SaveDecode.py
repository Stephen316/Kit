from os import link as LinkFile, replace as ReplaceFile
from pathlib import Path as FilePath
from tempfile import NamedTemporaryFile


def SaveDecode(Destination: FilePath, Content: str, Overwrite: bool) -> None:
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=Destination.parent, prefix=".kit-", delete=False
    ) as Output:
        TempPath = FilePath(Output.name)
        try:
            _ = Output.write(Content + "\n")
            Output.close()
            if Overwrite:
                ReplaceFile(TempPath, Destination)
            else:
                LinkFile(TempPath, Destination)
        finally:
            TempPath.unlink(missing_ok=True)
