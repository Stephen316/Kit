from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import convert as ConvertFile
from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.solidworks import SldprtArchive
from convert.adapters.solidworks import build_sldprt as BuildSldprt
from convert.adapters.solidworks.Container.Container import container_signatures as ContainerSignatures
from convert.adapters.solidworks.Core.BindInch import KUnresolvedInchDimension
from tests.Convert.Api.ApiTestPaths import KRootPath


# conflicting equation tokens remove the typed bindings while leaving inch display values readable
def UnboundInch(TmpPath: FilePath) -> FilePath:
    Original = (
        KRootPath
        / "re/automation/PairedCaptures/P04/solidworks-c1986308375a"
        / "P04-solidworks-units-inch.SLDPRT"
    ).read_bytes()
    Archive = SldprtArchive.from_bytes(Original)
    Streams = Archive.streams
    StreamName = "Contents/Config-0"
    Before = '"cut_left_mm@CutSketch" ='.encode("utf-16le")
    After = '"bad_left_mm@CutSketch" ='.encode("utf-16le")
    assert len(Before) == len(After) and Streams[StreamName].count(Before) == 1
    Streams[StreamName] = Streams[StreamName].replace(Before, After, 1)
    SourcePath = TmpPath / "Unbound.SLDPRT"
    _ = SourcePath.write_bytes(
        BuildSldprt(
            Streams, file_id=Archive.file_id, format_version=Archive.format_version,
            signatures=ContainerSignatures(Original),
        )
    )
    return SourcePath


# unbound inch display lengths must prevent writes before the destination changes
def TestInchWrite(TmpPath: FilePath) -> None:
    SourcePath = UnboundInch(TmpPath)
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


# serialized inch uncertainty must stay actionable after the source format is relabeled
def TestRelabelInch(TmpPath: FilePath) -> None:
    Original = OpenDocument(UnboundInch(TmpPath))
    Document = ReplaceData(
        Original, source=ReplaceData(Original.source, format_id="interchange.json")
    )
    SourcePath = TmpPath / "Source.json"
    _ = SourcePath.write_text(Document.to_json(), encoding="utf-8")
    Document = OpenDocument(SourcePath)
    assert any(
        Parameter.attributes.get(KUnresolvedInchDimension) is True
        for Parameter in Document.parameters
    )
    TargetPath = TmpPath / "Target.json"
    _ = TargetPath.write_bytes(b"existing destination")
    with RaisesError(ValueError, match="unresolved SOLIDWORKS inch dimensions"):
        _ = WriteDocument(Document, TargetPath, overwrite=True, validate=False)
    with RaisesError(ValueError, match="unresolved SOLIDWORKS inch dimensions"):
        _ = ConvertFile(SourcePath, TargetPath, overwrite=True)
    assert TargetPath.read_bytes() == b"existing destination"
