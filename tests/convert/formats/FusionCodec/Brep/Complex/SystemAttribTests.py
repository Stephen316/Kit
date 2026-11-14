from dataclasses import replace as ReplaceValue
from math import isfinite as IsFinite
from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Attributes.StitchAttrib import (
    StitchAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.VertedgeAttrib import (
    KVertedgeCap,
    VertedgeAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from tests.convert.formats.FusionCodec.Brep.Complex.ComplexMembers import (
    ComplexMember,
)

KStitchMembers = (
    (
        "re/Fusion/Study/patchcontinuity-b9b0be85a281/brep_curvature.f3d",
        "4a3012e2629eb0ac68d8be61634279e07caed4daaef927ab1ff973fec745d8f8",
    ),
    (
        "re/Fusion/Study/patchcontinuity-b9b0be85a281/brep_tangent.f3d",
        "2f998919aea3be8fd9e22d399b0fa8c81dcc264d0c9f82176e6f818384f78e32",
    ),
)
KVertedgeMember = (
    "re/Fusion/Study/splines-9a18bae21127/splines.f3d",
    "b03c64905f0419137307e0e1cf74b2d84f9fa107c7e4f59f3ff1b5947c04a298",
)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Digest", KStitchMembers)
def TestStitchHint(Relative: str, Digest: str) -> None:
    Payload = ComplexMember(Relative, "smb", Digest)
    Geometry = ReadGeometry(Payload)
    Hints = tuple(
        (Index, Value)
        for Index, Value in enumerate(Geometry.Entities)
        if isinstance(Value, StitchAttrib)
    )
    assert len(Hints) == 1
    Index, Value = Hints[0]
    assert isinstance(Geometry.Entities[Value.Links.OwnerRef], EdgeNode)
    assert len(Value.HintValues) == 3
    assert all(IsFinite(Number) for Number in Value.HintValues)
    assert Value.HintValues[0] > 0.0
    Entities = list(Geometry.Entities)
    Entities[Index] = ReplaceValue(
        Value, HintValues=(float("nan"), *Value.HintValues[1:])
    )
    with RaisesError(ValueError):
        _ = EmitGeometry(ReplaceValue(Geometry, Entities=tuple(Entities)))
    assert EmitGeometry(Geometry) == Payload


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestVertedge() -> None:
    Payload = ComplexMember(KVertedgeMember[0], "smb", KVertedgeMember[1])
    Geometry = ReadGeometry(Payload)
    Lists = tuple(
        (Index, Value)
        for Index, Value in enumerate(Geometry.Entities)
        if isinstance(Value, VertedgeAttrib)
    )
    assert len(Lists) == 1
    Index, Value = Lists[0]
    assert isinstance(Geometry.Entities[Value.Links.OwnerRef], VertexNode)
    Edges = tuple(EdgeRef for EdgeRef, _ in Value.EdgeSlots if EdgeRef >= 0)
    assert Edges and all(
        isinstance(Geometry.Entities[EdgeRef], EdgeNode) for EdgeRef in Edges
    )
    Entities = list(Geometry.Entities)
    Entities[Index] = ReplaceValue(
        Value, EdgeSlots=(Value.EdgeSlots[0],) * (KVertedgeCap + 1)
    )
    with RaisesError(ValueError):
        _ = EmitGeometry(ReplaceValue(Geometry, Entities=tuple(Entities)))
    assert EmitGeometry(Geometry) == Payload
