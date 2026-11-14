from math import isclose, isfinite
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Validation.CheckSymMap import CheckSymMap


def CheckSymmetry(Surface: TsplineSurface) -> None:
    Symmetry = Surface.Symmetry
    if Symmetry is None:
        return
    Frame = (Symmetry.Origin, Symmetry.FirstAxis, Symmetry.SecondAxis)
    if tuple(Value.Weight for Value in Frame) != (1.0, 0.0, 0.0):
        raise ValueError("Invalid TSM homogeneous symmetry frame")
    if any(
        not all(isfinite(Coord) for Coord in (Value.CoordX, Value.CoordY, Value.CoordZ))
        for Value in Frame
    ):
        raise ValueError("Invalid TSM symmetry coordinates")
    First = (Frame[1].CoordX, Frame[1].CoordY, Frame[1].CoordZ)
    Second = (Frame[2].CoordX, Frame[2].CoordY, Frame[2].CoordZ)
    if not all(
        isclose(sum(Coord * Coord for Coord in Vector), 1.0, rel_tol=0.0, abs_tol=1e-12)
        for Vector in (First, Second)
    ):
        raise ValueError("TSM symmetry axes are not unit vectors")
    if (
        abs(
            sum(
                FirstValue * SecondValue
                for FirstValue, SecondValue in zip(First, Second, strict=True)
            )
        )
        > 1e-12
    ):
        raise ValueError("TSM symmetry axes are not orthogonal")
    CheckSymMap(Symmetry.FaceMap, len(Surface.Topology.Faces))
    CheckSymMap(Symmetry.EdgeMap, len(Surface.Topology.Edges))
    CheckSymMap(Symmetry.VertexMap, len(Surface.Topology.Vertices))
