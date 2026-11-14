from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import convert as ConvertFile
from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from tests.convert.api.ApiTestPaths import KSamplePath


def TestBoundWrite(TmpPath: FilePath) -> None:
    NeutralPath = TmpPath / "Neutral.json"
    Result = ConvertFile(KSamplePath, NeutralPath)
    assert OpenDocument(NeutralPath) == Result.document


def TestMissingLink(TmpPath: FilePath) -> None:
    Original = OpenDocument(KSamplePath)
    Parameter, *Remaining = Original.parameters
    Marked = ReplaceData(
        Parameter,
        attributes={
            **Parameter.attributes,
            "unresolved_equation_references": ("MissingDimension@Sketch1",),
        },
    )
    Document = ReplaceData(Original, parameters=(Marked, *Remaining))
    SourcePath = TmpPath / "Research.json"
    TargetPath = TmpPath / "Target.json"
    _ = TargetPath.write_bytes(b"existing destination")
    _ = SourcePath.write_text(Document.to_json(), encoding="utf-8")
    assert OpenDocument(SourcePath) == Document
    with RaisesError(ValueError, match="unresolved SOLIDWORKS equation references"):
        _ = WriteDocument(Document, TargetPath, overwrite=True)
    with RaisesError(ValueError, match="MissingDimension@Sketch1"):
        _ = ConvertFile(SourcePath, TargetPath, overwrite=True)
    assert TargetPath.read_bytes() == b"existing destination"

