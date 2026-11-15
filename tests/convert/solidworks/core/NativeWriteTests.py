from pathlib import Path as FilePath

from pytest import mark as TestMark, raises as RaisesError

from convert import convert as ConvertFile
from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from interchange.document.models.DocumentWalk import WalkDocuments
from interchange.features.FeatureKinds import NativeFeature
from tests.convert.api.Fusion.AdapterCases import AdapterCase
from tests.convert.solidworks.core.NativeWrites.NativeHistory import NativeHistory
from tests.convert.solidworks.core.NestedDocument import NestedDocument
from tests.convert.solidworks.core.RejectWrites import RejectWrites


# native history must stay blocked in nested and suppressed feature scenarios
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("IsSuppressed", (False, True))
def TestNativeWrite(TmpPath: FilePath, IsNested: bool, IsSuppressed: bool) -> None:
    Document = NativeHistory(IsSuppressed)
    if IsNested:
        Document = NestedDocument(AdapterCase("rectangle"), Document)
    SourcePath = TmpPath / "Source.json"
    _ = SourcePath.write_text(Document.to_json(), encoding="utf-8")
    Document = OpenDocument(SourcePath)
    NativeSteps = [
        StepValue
        for PartValue in WalkDocuments(Document)
        for StepValue in PartValue.feature_timeline
        if isinstance(StepValue.definition, NativeFeature)
    ]
    assert len(NativeSteps) == 1
    assert NativeSteps[0].suppressed is IsSuppressed
    TargetPath = TmpPath / "Public.json"
    _ = TargetPath.write_bytes(b"existing public destination")
    with RaisesError(ValueError, match="native-only feature definitions"):
        _ = WriteDocument(Document, TargetPath, overwrite=True, validate=False)
    with RaisesError(ValueError, match="native-only feature definitions"):
        _ = ConvertFile(SourcePath, TargetPath, overwrite=True)
    assert TargetPath.read_bytes() == b"existing public destination"
    RejectWrites(Document, TmpPath, "native-only feature definitions")
