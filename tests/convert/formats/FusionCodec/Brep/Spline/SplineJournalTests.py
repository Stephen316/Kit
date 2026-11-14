from dataclasses import replace as ReplaceValue
from sys import version_info as PythonVersion

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import (
    MapSubtypes,
    WalkSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListPrograms import ListPrograms
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListSubtypes import ListSubtypes
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.convert.formats.FusionCodec.Brep.Spline.SplineMembers import SplineMembers


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Form archive requires ZIP Zstandard"
)
def TestSplineParts() -> None:
    Count = 0
    for NameValue, Payload, Program in SplineMembers():
        if NameValue.endswith(".smb"):
            Geometry = ReadGeometry(Payload)
            assert EmitGeometry(Geometry) == Payload
            Entities = Geometry.Entities
        else:
            Journal = ReadJournal(Payload)
            assert EmitJournal(Journal) == Payload
            Entities = Journal.Entities
        assert any(isinstance(Value, SplineNode) for Value in Entities)
        assert ListPrograms(Entities) == (ReadTspline(Program),)
        Count += 1
    assert Count == 66


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Form archive requires ZIP Zstandard"
)
@MarkTests.parametrize("Fault", ("forward", "kind"))
def TestSubtypeRefs(Fault: str) -> None:
    Payload = next(Value[1] for Value in SplineMembers() if Value[0].endswith(".smb"))
    Geometry = ReadGeometry(Payload)
    Index, Value, Support = next(
        (Index, Value, Found)
        for Index, Value in enumerate(Geometry.Entities)
        if isinstance(Value, PcurveNode)
        for Found in WalkSubtypes(Value.Curve)
        if isinstance(Found, SubtypeRef)
    )
    assert Support.Family == "surface"
    Kinds = [
        KindName
        for Entity in Geometry.Entities
        for KindName, Reference in ListSubtypes(Entity)
        if Reference is None
    ]
    Target = 4096 if Fault == "forward" else Kinds.index("exact_int_cur")
    Curve = MapSubtypes(Value.Curve, {Support.Index: Target})
    assert isinstance(Curve, SubtypeNode)
    Entities = list(Geometry.Entities)
    Entities[Index] = ReplaceValue(Value, Curve=Curve)
    with RaisesError(ValueError):
        _ = EmitGeometry(ReplaceValue(Geometry, Entities=tuple(Entities)))
