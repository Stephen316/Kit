from convert.formats.Fusion.TSplineCodec.Model.PlaneSymmetry import PlaneSymmetry
from convert.formats.Fusion.TSplineCodec.Writing.WritePairs import WritePairs
from convert.formats.Fusion.TSplineCodec.Writing.WritePoint import WritePoint


def WriteSymmetry(Symmetry: PlaneSymmetry | None) -> tuple[str, ...]:
    if Symmetry is None:
        return ()
    Plane = "105plane " + " ".join(
        WritePoint(Value)
        for Value in (Symmetry.Origin, Symmetry.FirstAxis, Symmetry.SecondAxis)
    )
    return (
        "105sym 0",
        Plane,
        WritePairs("fr", Symmetry.FaceMap.Reverse),
        WritePairs("er", Symmetry.EdgeMap.Reverse),
        WritePairs("vr", Symmetry.VertexMap.Reverse),
        WritePairs("f", Symmetry.FaceMap.Forward),
        WritePairs("e", Symmetry.EdgeMap.Forward),
        WritePairs("v", Symmetry.VertexMap.Forward),
    )
