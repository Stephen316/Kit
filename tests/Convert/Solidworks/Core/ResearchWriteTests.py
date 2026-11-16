from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import convert as ConvertFile
from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.registry.ResearchWrite import KResearchReadStatus
from tests.Convert.Api.ApiTestPaths import KSamplePath


# research output must remain inspectable while public reexport stays blocked
def TestResearch(TmpPath: FilePath) -> None:
    Original = OpenDocument(KSamplePath)
    Document = ReplaceData(
        Original,
        metadata={**Original.metadata, KResearchReadStatus: "unqualified"},
    )
    ResearchPath = TmpPath / "Evidence.json"
    TargetPath = TmpPath / "Target.json"
    _ = ResearchPath.write_text(Document.to_json(), encoding="utf-8")
    _ = TargetPath.write_bytes(b"existing destination")
    Evidence = OpenDocument(ResearchPath)
    assert Evidence.metadata[KResearchReadStatus] == "unqualified"
    with RaisesError(ValueError, match="unqualified research documents"):
        _ = WriteDocument(Evidence, TargetPath, overwrite=True)
    with RaisesError(ValueError, match="unqualified research documents"):
        _ = ConvertFile(ResearchPath, TargetPath, overwrite=True)
    assert TargetPath.read_bytes() == b"existing destination"
