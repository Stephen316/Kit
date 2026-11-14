from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import convert as ConvertFile
from convert import open_document as OpenDocument
from convert.adapters.solidworks.core.BindInch import KUnresolvedInchDimension
from tests.convert.api.ApiTestPaths import KRootPath


def TestInchWrite(TmpPath: FilePath) -> None:
    SourcePath = (
        KRootPath
        / "re/automation/PairedCaptures/P04/solidworks-c1986308375a"
        / "P04-solidworks-units-inch.SLDPRT"
    )
    Document = OpenDocument(SourcePath)
    Unresolved = {
        Parameter.name
        for Parameter in Document.parameters
        if Parameter.attributes.get(KUnresolvedInchDimension) is True
        and Parameter.value.unit == "in"
    }
    assert Unresolved >= {
        "width_mm",
        "height_mm",
        "cut_width_mm",
        "cut_height_mm",
        "cut_left_mm",
        "cut_bottom_mm",
    }
    TargetPath = TmpPath / "Target.json"
    _ = TargetPath.write_bytes(b"existing destination")
    with RaisesError(ValueError, match="unresolved SOLIDWORKS inch dimensions"):
        _ = ConvertFile(SourcePath, TargetPath, overwrite=True)
    assert TargetPath.read_bytes() == b"existing destination"
