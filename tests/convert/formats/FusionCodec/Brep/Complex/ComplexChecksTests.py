from dataclasses import replace as ReplaceValue
from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TedgeNode import TedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TvertexNode import (
    TvertexNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from tests.convert.formats.FusionCodec.Brep.Complex.ComplexMembers import (
    ComplexMember,
)

KFormMember = (
    "re/Fusion/Study/sweepnurbspaths-7ded30a4b9ae/polynomial_cubic.f3d",
    "c014a71a3bdaef07af2597234d1a15bc077ff57781bd9a48486f02769ec679e7",
)
KTolerantMember = (
    "re/Fusion/Study/solidsweeps-7d2677669e3d/solid_twist.f3d",
    "ae2a84121182b35d76cffa413c2eb74390a36af5969556522fb2b2a7b7fdcbd1",
)


def SwapEntity(
    Geometry: GeometryState, Index: int, Value: KJournalEntity
) -> GeometryState:
    Entities = list(Geometry.Entities)
    Entities[Index] = Value
    return ReplaceValue(Geometry, Entities=tuple(Entities))


def FormIndex(Geometry: GeometryState) -> int:
    for Value in Geometry.Entities:
        if isinstance(Value, CoedgeNode) and Value.Pcurve >= 0:
            Pcurve = Geometry.Entities[Value.Pcurve]
            if isinstance(Pcurve, PcurveNode) and Pcurve.Form:
                return Value.Pcurve
    raise ValueError("Fixture has no referenced pcurve form")


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestFormSign() -> None:
    Payload = ComplexMember(KFormMember[0], "smb", KFormMember[1])
    Geometry = ReadGeometry(Payload)
    Index = FormIndex(Geometry)
    Pcurve = Geometry.Entities[Index]
    assert isinstance(Pcurve, PcurveNode)
    assert not Pcurve.Reversed
    Flipped = SwapEntity(Geometry, Index, ReplaceValue(Pcurve, Form=-Pcurve.Form))
    with RaisesError(ValueError, match="form sign"):
        _ = EmitGeometry(Flipped)
    assert EmitGeometry(Geometry) == Payload


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestTvertexGap() -> None:
    Payload = ComplexMember(KTolerantMember[0], "smb", KTolerantMember[1])
    Geometry = ReadGeometry(Payload)
    Index, Vertex = next(
        (Index, Value)
        for Index, Value in enumerate(Geometry.Entities)
        if isinstance(Value, TvertexNode)
    )
    Adjacent = tuple(
        Value.Tolerance
        for Value in Geometry.Entities
        if isinstance(Value, TedgeNode)
        and Index in (Value.Base.StartVertex, Value.Base.EndVertex)
    )
    assert Adjacent and Vertex.Tolerance >= max(Adjacent)
    Tighter = min(Adjacent) / 2.0
    with RaisesError(ValueError, match="tighter"):
        _ = EmitGeometry(
            SwapEntity(
                Geometry,
                Index,
                ReplaceValue(Vertex, Tolerance=Tighter, SavedTolerance=Tighter),
            )
        )
    Looser = SwapEntity(
        Geometry,
        Index,
        ReplaceValue(
            Vertex, Tolerance=Vertex.Tolerance * 2.0, SavedTolerance=Vertex.Tolerance
        ),
    )
    assert ReadGeometry(EmitGeometry(Looser)) == Looser
    assert EmitGeometry(Geometry) == Payload
