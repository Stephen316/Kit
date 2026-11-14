from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath
from typing import cast as CastValue

from convert import open_document as OpenDocument, write_document as WriteDocument
from tests.convert.api.Fusion.AdapterCases import AdapterCase


def TestLegacyState(TmpPath: FilePath) -> None:
    Source = TmpPath / "Source.f3d"
    _ = WriteDocument(AdapterCase("parameter"), Source, destination_format="f3d")
    Document = OpenDocument(Source)
    Contract = dict(
        CastValue(dict[str, object], Document.metadata["fusion.native_state"])
    )
    Model = dict(CastValue(dict[str, object], Contract["model"]))
    Fields = dict(CastValue(dict[str, object], Model["fields"]))
    del Fields["Meshes"]
    del Fields["Forms"]
    Segments = CastValue(dict[str, list[dict[str, object]]], Fields["Segments"])
    Fields["Segments"] = {
        "tuple": [
            {
                **SegmentItem,
                "fields": {
                    FieldKey: FieldValue
                    for FieldKey, FieldValue in CastValue(
                        dict[str, object], SegmentItem["fields"]
                    ).items()
                    if FieldKey != "BulkSlack"
                },
            }
            for SegmentItem in Segments["tuple"]
        ]
    }
    Contract["model"] = {**Model, "fields": Fields}
    Legacy = ReplaceData(Document, metadata={"fusion.native_state": Contract})
    Target = TmpPath / "Restored.f3d"
    _ = WriteDocument(Legacy, Target, destination_format="f3d")
    assert Target.read_bytes() == Source.read_bytes()
