from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument, write_document as WriteDocument
from interchange import CadDocument
from interchange.serialization import from_data as FromData, to_data as ToData
from tests.convert.api.Fusion.AdapterCases import AdapterCase


@MarkTests.parametrize("Attack", ("version", "record", "extra"))
def TestStateReject(TmpPath: FilePath, Attack: str) -> None:
    Source = TmpPath / "Source.f3d"
    _ = WriteDocument(AdapterCase("parameter"), Source, destination_format="f3d")
    Document = OpenDocument(Source)
    State: dict[str, object] = {
        "version": 1,
        "model": {"record": "os.system", "fields": {}},
    }
    if Attack == "version":
        State["version"] = 2
    if Attack == "extra":
        State["archive"] = b"unaccounted archive"
    Altered = ReplaceData(Document, metadata={"fusion.native_state": State})
    Target = TmpPath / "Rejected.f3d"
    with RaisesError(ValueError):
        _ = WriteDocument(Altered, Target, destination_format="f3d")
    assert not Target.exists()


def TestOldNeutral(TmpPath: FilePath) -> None:
    Document = AdapterCase("parameter")
    WireValue = ToData(Document)
    if not isinstance(WireValue, dict):
        raise AssertionError("neutral document must serialize to a record")
    _ = WireValue.pop("materials")
    Loaded = FromData(WireValue)
    assert isinstance(Loaded, CadDocument) and Loaded.materials == ()
    Target = TmpPath / "Parameter.f3d"
    _ = WriteDocument(Loaded, Target, destination_format="f3d")
    assert OpenDocument(Target).parameters[0].value == Document.parameters[0].value
