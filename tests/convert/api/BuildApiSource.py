from pathlib import Path as FilePath

from convert import write_document as WriteDocument
from tests.convert.api.Fusion.AdapterCases import AdapterCase


def BuildApiSource(TmpPath: FilePath) -> FilePath:
    SourcePath = TmpPath / "Source.f3d"
    _ = WriteDocument(
        AdapterCase("rectangle"),
        SourcePath,
        destination_format="f3d",
        allow_carrier=False,
    )
    return SourcePath
