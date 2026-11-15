from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

from pytest import mark as TestMark, raises as RaisesError

from convert import convert as ConvertFile
from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.registry.ResearchWrite import KResearchReadStatus
from convert.adapters.solidworks.core.Native import (
    KStreamOrderSupportSource,
    KUnresolvedSupportSource,
)
from convert.adapters.solidworks.core.OrdinaryRead import KArchiveSupport
from tests.convert.api.ApiTestPaths import KRootPath, KSamplePath
from tests.convert.solidworks.core.NestedDocument import NestedDocument
from tests.convert.solidworks.core.RejectWrites import RejectWrites


# typed placement and unframed support both retain the current qualification boundary
@TestMark.parametrize(
    ("NativePath", "SupportSources"),
    (
        (
            "P01/solidworks-75b9308cf13e/P01-solidworks-plane-yz.SLDPRT",
            (KArchiveSupport,),
        ),
        (
            "P03/solidworks-db1390476325/P03-solidworks-plane-yz.SLDPRT",
            (KArchiveSupport,),
        ),
        (
            "P04/solidworks-c1986308375a/P04-solidworks-plane-yz.SLDPRT",
            (KStreamOrderSupportSource, KUnresolvedSupportSource),
        ),
    ),
)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("RelabelSource", (False, True))
def TestSupportGate(
    TmpPath: FilePath, NativePath: str, SupportSources: tuple[str, ...],
    IsNested: bool, RelabelSource: bool
) -> None:
    Marked = OpenDocument(KRootPath / "re/automation/PairedCaptures" / NativePath)
    assert Marked.metadata.get(KResearchReadStatus) != "unqualified"
    assert any(
        Sketch.attributes.get("support_plane_source")
        in SupportSources
        for Sketch in Marked.sketches
    )
    if RelabelSource:
        Marked = ReplaceData(
            Marked,
            source=ReplaceData(Marked.source, format_id="interchange.json"),
            sketches=tuple(
                ReplaceData(Sketch, provenance=None) for Sketch in Marked.sketches
            ),
        )
    Document = NestedDocument(OpenDocument(KSamplePath), Marked) if IsNested else Marked
    SourcePath = TmpPath / "Source.json"
    _ = SourcePath.write_text(Document.to_json(), encoding="utf-8")
    Document = OpenDocument(SourcePath)
    TargetPath = TmpPath / "Public.json"
    _ = TargetPath.write_bytes(b"existing public destination")
    with RaisesError(ValueError, match="unqualified SOLIDWORKS sketch support"):
        _ = WriteDocument(Document, TargetPath, overwrite=True, validate=False)
    with RaisesError(ValueError, match="unqualified SOLIDWORKS sketch support"):
        _ = ConvertFile(SourcePath, TargetPath, overwrite=True)
    assert TargetPath.read_bytes() == b"existing public destination"
    RejectWrites(Document, TmpPath, "unqualified SOLIDWORKS sketch support")
