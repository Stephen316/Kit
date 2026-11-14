from convert.formats.Fusion.MeshCodec.Model.FaceGroup import FaceGroup
from convert.formats.Fusion.MeshCodec.Model.FeatureEdge import FeatureEdge
from convert.formats.Fusion.MeshCodec.Model.MeshPoint import MeshPoint
from convert.formats.Fusion.MeshCodec.Model.MeshRegistry import MeshRegistry
from convert.formats.Fusion.MeshCodec.Model.OctaNormal import OctaNormal
from convert.formats.Fusion.MeshCodec.Model.ParaMesh import ParaMesh


def AuthoredMesh() -> ParaMesh:
    Registry = MeshRegistry(
        "b8e63e79-79f0-4cbc-8e89-c89204dbf349",
        "60f9360a-0c75-4d97-8413-818c84c029c0",
        "ea42e5f6-7cef-48d8-9811-9fb4db1783cf",
        1,
        "points",
        "corners",
        "normals",
        "overrides",
        "edges",
        "groups",
        (FaceGroup(29, "fb707054-8774-4c2c-9b56-dd6ba197000b"),),
        ("normals", "edges", "corners", "points", "groups", "overrides"),
    )
    Positions = (
        MeshPoint(0.0, 0.0, 0.0),
        MeshPoint(2.0, 0.0, 0.0),
        MeshPoint(0.0, 3.0, 0.0),
        MeshPoint(0.0, 0.0, 5.0),
    )
    return ParaMesh(
        Registry,
        Positions,
        (0, 2, 1, 0, 1, 3, 1, 2, 3, 2, 0, 3),
        47,
        (OctaNormal(0.0, 0.0),) * 4,
        (),
        tuple(
            FeatureEdge(First, Second)
            for First, Second in ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
        ),
        (29, 29, 29, 29),
    )
