from collections import Counter
from math import pi as KCircleHalf
from pathlib import Path as FilePath

from pytest import approx as Approx
from pytest import mark as TestMarks
from pytest import raises as RaiseError

from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.EmitCylinderSmb import EmitCylinderSmb
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import IsAsmFlag
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmNum
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmVec
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable

KGeometryStamp = GeometryStamp("Kit", "Geometry integration", "2026-11-12T00:00:00Z")


@TestMarks.parametrize(
    ("Radius", "Height", "BasePoint"),
    (
        (15, 11, (20, -30, 5)),
        (7.5, 18.25, (1.25, 2.5, 3.75)),
        (25.5, 4.5, (-15.5, 6.25, -2.5)),
    ),
)
def TestSmbArchive(
    TmpPath: FilePath,
    Radius: float,
    Height: float,
    BasePoint: tuple[float, float, float],
) -> None:
    Model = CylinderBody(Radius, Height, BasePoint)
    Target = TmpPath / "IndependentCylinder.smb"
    _ = Target.write_bytes(EmitCylinderSmb(Model, KGeometryStamp))
    Table = ReadAsmTable(Target.read_bytes())
    assert Table.RootCount == 2
    Counts = Counter(Record.Name for Record in Table.Records)
    assert (Counts["body"], Counts["face"], Counts["edge"], Counts["vertex"]) == (
        1,
        3,
        2,
        2,
    )
    Edges = tuple(Record for Record in Table.Records if Record.Name == "edge")
    Curves = tuple(
        RequireAsm(Table, ReadAsmPtr(Record, 8), "ellipse-curve", 9) for Record in Edges
    )
    Centers = tuple(ReadAsmVec(Record, 3, 19) for Record in Curves)
    RadiusVectors = tuple(ReadAsmVec(Record, 5, 20) for Record in Curves)
    assert tuple(Vector.x for Vector in RadiusVectors) == Approx(
        (Radius / 10, Radius / 10)
    )
    assert all(Vector.y == Vector.z == 0 for Vector in RadiusVectors)
    SpanHeight = abs(Centers[0].z - Centers[1].z)
    assert SpanHeight == Approx(Height / 10)
    Volume = KCircleHalf * RadiusVectors[0].x ** 2 * SpanHeight
    assert Volume == Approx(KCircleHalf * Radius**2 * Height / 1000)
    CenterMass = (Centers[0].x, Centers[0].y, (Centers[0].z + Centers[1].z) / 2)
    assert CenterMass == Approx(
        (BasePoint[0] / 10, BasePoint[1] / 10, (BasePoint[2] + Height / 2) / 10)
    )
    Surface = next(Record for Record in Table.Records if Record.Name == "cone-surface")
    assert ReadAsmNum(Surface, 11) == Approx(Radius / 10)
    for Plane in (Record for Record in Table.Records if Record.Name == "plane-surface"):
        Reference = ReadAsmVec(Plane, 5, 20)
        assert (Reference.x, Reference.y, Reference.z) == (1, 0, 0)


def TestSmbLinks() -> None:
    Model = CylinderBody(12.5, 16.75, (-3.5, 4.5, 2.5))
    Table = ReadAsmTable(EmitCylinderSmb(Model, KGeometryStamp))
    assert len(Table.Records) == 26
    BodyRoot = RequireAsm(Table, 1, "body", 6)
    LumpRoot = RequireAsm(Table, ReadAsmPtr(BodyRoot, 3), "lump", 6)
    assert ReadAsmPtr(LumpRoot, 5) == 1
    ShellRoot = RequireAsm(Table, ReadAsmPtr(LumpRoot, 4), "shell", 8)
    assert RequireAsm(Table, ReadAsmPtr(ShellRoot, 5), "face", 10)
    for Identity, Record in enumerate(Table.Records):
        for Index, Token in enumerate(Record.Tokens):
            if Token[0] == 12:
                assert -1 <= ReadAsmPtr(Record, Index) < len(Table.Records)
        if Record.Name == "coedge":
            Partner = RequireAsm(Table, ReadAsmPtr(Record, 5), "coedge", 11)
            assert ReadAsmPtr(Partner, 5) == Identity
            assert ReadAsmPtr(Partner, 6) == ReadAsmPtr(Record, 6)
            assert IsAsmFlag(Partner, 7) != IsAsmFlag(Record, 7)
        if Record.Name == "edge":
            assert ReadAsmPtr(Record, 3) == ReadAsmPtr(Record, 5)
            assert ReadAsmNum(Record, 4) == -KCircleHalf
            assert ReadAsmNum(Record, 6) == KCircleHalf


@TestMarks.parametrize("Suffix", (b"\x00", b"\x11", b"trailing"))
def TestSmbTrailing(Suffix: bytes) -> None:
    Model = CylinderBody(4.5, 6.25, (1.5, 2.5, 3.5))
    Payload = EmitCylinderSmb(Model, KGeometryStamp)
    with RaiseError(ValueError):
        _ = ReadAsmTable(Payload + Suffix)
