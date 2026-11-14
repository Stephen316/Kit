from math import cos as Cosine, sin as SineValue, atan2 as ArcTangent
from pathlib import Path as FilePath

from pytest import approx as Approx, mark as TestMarks

from convert.formats.Fusion.GeometryCodec.Frustum.EmitFrustumSmt import EmitFrustumSmt
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


@TestMarks.parametrize("TopRadius", (8.0, 10.0, 14.0))
def TestFrustumText(TmpPath: FilePath, TopRadius: float) -> None:
    Model = FrustumBody(10.0, TopRadius, 17.0, (20.0, -30.0, 5.0))
    Stamp = GeometryStamp("Kit", "Frustum text integration", "2026-11-12T00:00:00Z")
    Target = TmpPath / "IndependentFrustum.smt"
    _ = Target.write_bytes(EmitFrustumSmt(Model, Stamp))
    Lines = Target.read_text().splitlines()
    assert Lines[0] == "23200 0 2 2"
    assert Lines[2] == "1 1e-6 1e-10"
    assert Lines[-1] == "End-of-ASM-data"
    assert len(Lines[3:-1]) == 26
    assert all(LineValue.endswith(" #") for LineValue in Lines[3:-1])
    Fields = next(
        LineValue.split()
        for LineValue in Lines
        if LineValue.startswith("cone-surface ")
    )
    assert tuple(map(float, Fields[4:7])) == (20.0, -30.0, 5.0)
    assert tuple(map(float, Fields[10:14])) == (10.0, 0.0, 0.0, 1.0)
    Angle = ArcTangent(TopRadius - 10.0, 17.0)
    assert tuple(map(float, Fields[16:19])) == Approx(
        (SineValue(Angle), Cosine(Angle), 10.0)
    )
    assert Fields[19:] == ["forward", "I", "I", "I", "I", "#"]
    Curves = [
        LineValue.split()
        for LineValue in Lines
        if LineValue.startswith("ellipse-curve ")
    ]
    assert tuple(float(Fields[10]) for Fields in Curves) == (TopRadius, 10.0)
