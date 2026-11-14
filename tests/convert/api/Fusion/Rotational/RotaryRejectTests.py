from interchange.geometry.models.GeometryCurves import CircleGeometry

from dataclasses import replace as ReplaceData
from io import BytesIO as ByteStream
from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.api.Fusion.Rotational.ChangeRotary import ChangeRotary, ChangeSnapTag
from tests.convert.api.Fusion.Rotational.RotaryCase import (
    KRotaryCases,
    RotaryCase,
    RotarySource,
)


@MarkTests.parametrize("CaseValue", KRotaryCases)
def TestRotaryLinks(TmpPath: FilePath, CaseValue: RotaryCase) -> None:
    Source = RotarySource(CaseValue)
    Document = OpenDocument(Source)
    Changed = ChangeRotary(ReadDocument(Source.read_bytes()), CaseValue.RoleName)
    Archive = EmitParsed(Changed)
    with RaisesError(ValueError):
        _ = OpenDocument(ByteStream(Archive), source_format="f3d")
    Altered = ReplaceData(
        Document,
        metadata={"fusion.native_state": {"version": 2, "model": EncodeState(Changed)}},
    )
    Target = TmpPath / "Preserved.f3d"
    _ = Target.write_bytes(b"preserved destination")
    with RaisesError(ValueError):
        _ = WriteDocument(Altered, Target, destination_format="f3d", overwrite=True)
    assert Target.read_bytes() == b"preserved destination"
    assert tuple(TmpPath.iterdir()) == (Target,)


@MarkTests.parametrize("CaseValue", (KRotaryCases[0], KRotaryCases[2]))
def TestRotaryTags(CaseValue: RotaryCase) -> None:
    Source = RotarySource(CaseValue)
    Changed = ChangeSnapTag(ReadDocument(Source.read_bytes()))
    Archive = EmitParsed(Changed)
    with RaisesError(ValueError):
        _ = OpenDocument(ByteStream(Archive), source_format="f3d")


@MarkTests.parametrize("CaseValue", KRotaryCases)
def TestRotaryEdit(CaseValue: RotaryCase) -> None:
    Document = OpenDocument(RotarySource(CaseValue))
    Sketch = Document.sketches[0]
    Circle = Sketch.entities[-1]
    if not isinstance(Circle.geometry, CircleGeometry):
        raise ValueError("Circular projection must expose actual circle geometry")
    Changed = ReplaceData(Circle, geometry=ReplaceData(Circle.geometry, radius=15.0))
    Altered = ReplaceData(
        Document,
        sketches=(ReplaceData(Sketch, entities=(*Sketch.entities[:-1], Changed)),),
    )
    Target = ByteStream(b"preserved stream")
    with RaisesError(ValueError):
        _ = WriteDocument(Altered, Target, destination_format="f3d")
    assert Target.getvalue() == b"preserved stream"
