from pathlib import Path as FilePath

from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
from convert.formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.CreatePolyBody import (
    CreatePolyBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from tests.convert.formats.FusionCodec.Brep.GeometryState.GeometryArchive import (
    GeometryArchive,
)
from tests.convert.formats.FusionCodec.Brep.Planar.PlanarSamples import (
    KPlanarHistory,
    KPlanarPlace,
    KPlanarStamp,
    MakeTetrahedron,
)


def TestStateExport(TmpPath: FilePath) -> None:
    Journal = CreatePolyBody(
        MakeTetrahedron(), KPlanarHistory, KPlanarStamp, KPlanarPlace
    )
    Payload = EmitStateSmb(Journal)
    Parsed = GeometryArchive(TmpPath / "ExportedState.zip", Payload)
    assert Parsed.Entities == Journal.Entities
    assert tuple(
        Value for Value in Parsed.Entities if isinstance(Value, TransformNode)
    ) == (KPlanarPlace,)
    assert EmitGeometry(Parsed) == Payload
