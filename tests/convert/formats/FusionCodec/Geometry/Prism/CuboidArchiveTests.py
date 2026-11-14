from collections import Counter
from pathlib import Path as FilePath

from pytest import approx as Approx, mark as TestMarks, raises as RaiseError

from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody
from convert.formats.Fusion.GeometryCodec.Prism.EmitCuboidSmb import EmitCuboidSmb
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    ReadAsmInt,
    ReadAsmPtr,
    RequireAsm,
)
from tests.convert.formats.FusionCodec.Geometry.Prism.PrismPlanes import CheckFacePlanes
from tests.convert.formats.FusionCodec.Geometry.Prism.PrismVolume import PrismVolume
from tests.convert.formats.FusionCodec.Geometry.Prism.ReadCuboid import ReadCuboid

KPrismStamp = GeometryStamp("Kit", "Prism integration", "2026-11-12T00:00:00Z")


@TestMarks.parametrize(
    "Lengths,BasePoint",
    (
        ((12.0, 18.0, 24.0), (20.0, -30.0, 5.0)),
        ((17.5, 23.25, 8.75), (-12.5, 7.25, 3.5)),
        ((3.5, 9.25, 1.75), (4.25, -2.5, -7.75)),
    ),
)
def TestCuboidShape(
    TmpPath: FilePath,
    Lengths: tuple[float, float, float],
    BasePoint: tuple[float, float, float],
) -> None:
    Target = TmpPath / "IndependentCuboid.smb"
    _ = Target.write_bytes(EmitCuboidSmb(CuboidBody(*Lengths, BasePoint), KPrismStamp))
    Evidence = ReadCuboid(Target.read_bytes())
    Counts = Counter(Record.Name for Record in Evidence.Table.Records)
    assert Evidence.Table.RootCount == 2
    assert (
        Counts["body"],
        Counts["face"],
        Counts["coedge"],
        Counts["edge"],
        Counts["vertex"],
    ) == (1, 6, 24, 12, 8)
    assert PrismVolume(Evidence) == Approx(Lengths[0] * Lengths[1] * Lengths[2])
    for AxisIndex, FieldName in enumerate(("x", "y", "z")):
        Coordinates = [getattr(Point, FieldName) for Point in Evidence.Points.values()]
        assert min(Coordinates) == Approx(BasePoint[AxisIndex])
        assert max(Coordinates) == Approx(BasePoint[AxisIndex] + Lengths[AxisIndex])
    CheckFacePlanes(Evidence)


def TestCuboidLinks() -> None:
    Evidence = ReadCuboid(
        EmitCuboidSmb(CuboidBody(17.5, 23.25, 8.75, (-12.5, 7.25, 3.5)), KPrismStamp)
    )
    for Identity, Record in enumerate(Evidence.Table.Records):
        for Index, Token in enumerate(Record.Tokens):
            if Token[0] == 12:
                assert -1 <= ReadAsmPtr(Record, Index) < len(Evidence.Table.Records)
        if Record.Name == "vertex":
            Owner = RequireAsm(Evidence.Table, ReadAsmPtr(Record, 3), "edge", 11)
            Endpoint = ReadAsmInt(Record, 4)
            assert Endpoint in (0, 1)
            assert ReadAsmPtr(Owner, 3 if Endpoint == 0 else 5) == Identity


def TestCuboidTail() -> None:
    Payload = EmitCuboidSmb(CuboidBody(1.5, 2.5, 3.5, (0, 0, 0)), KPrismStamp)
    with RaiseError(ValueError):
        _ = ReadCuboid(Payload + b"trailing")
