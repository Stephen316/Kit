from math import hypot as Hypot

from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    ReadAsmPtr,
    ReadAsmVec,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.PrismCarriers import CheckPrismPlane
from convert.geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface
from interchange.geometry.models.VectorSpace import SpaceVector
from tests.convert.formats.FusionCodec.Geometry.Prism.PrismEvidence import PrismEvidence
from tests.convert.formats.FusionCodec.Geometry.Prism.PrismVolume import PrismVertices


def CheckFacePlanes(Value: PrismEvidence) -> None:
    for FaceId in Value.Prism.Rings:
        Corners = PrismVertices(Value, FaceId)
        Tangent = OffsetVector(Corners[1], Corners[0], -1)
        Second = OffsetVector(Corners[2], Corners[0], -1)
        Normal = CrossVector(Tangent, Second)
        Length = Hypot(Normal.x, Normal.y, Normal.z)
        BasisLength = Hypot(Tangent.x, Tangent.y, Tangent.z)
        Expected = PlaneSurface(
            str(FaceId),
            Corners[0],
            SpaceVector(Normal.x / Length, Normal.y / Length, Normal.z / Length),
            SpaceVector(
                Tangent.x / BasisLength,
                Tangent.y / BasisLength,
                Tangent.z / BasisLength,
            ),
        )
        CheckPrismPlane(Value.Table, FaceId, Expected)
        FaceValue = RequireAsm(Value.Table, FaceId, "face", 10)
        Surface = RequireAsm(Value.Table, ReadAsmPtr(FaceValue, 7), "plane-surface", 11)
        assert DotVector(ReadAsmVec(Surface, 4, 20), Expected.normal) > 0.999999
