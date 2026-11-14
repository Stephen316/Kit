from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology


def GridPatches(
    Topology: CageTopology,
    Spokes: tuple[int, ...],
    Places: tuple[tuple[int, int], ...],
    Scale: int,
) -> tuple[PatchCell, ...]:
    Cells: list[PatchCell] = []
    for FaceIndex, FaceValue in enumerate(Topology.Faces):
        if FaceValue.IsHidden:
            raise ValueError("Fusion grid conversion does not convert hidden faces")
        LinkValue = Topology.Links[FaceValue.OriginLink]
        Following = Topology.Links[LinkValue.NextLink]
        if Spokes[FaceValue.OriginLink] != 3 or Spokes[LinkValue.NextLink] != 0:
            raise ValueError("Fusion grid conversion needs aligned face origins")
        ColumnIndex, RowIndex = Places[LinkValue.VertexIndex]
        if Places[Following.VertexIndex] != (ColumnIndex + 1, RowIndex):
            raise ValueError("Fusion grid conversion needs aligned face origins")
        Offset = (-RowIndex * Scale, -ColumnIndex * Scale, 0)
        Cells.append(PatchCell(FaceIndex, (0, Scale, 0, Scale), Offset))
    return tuple(Cells)
