from collections import Counter
from math import cos as Cosine, sin as SineValue

from pytest import approx as Approx

from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmNum,
    ReadAsmPtr,
    ReadAsmVec,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def CheckConeLinks(Table: AsmTable) -> None:
    Counts = Counter(Record.Name for Record in Table.Records)
    assert tuple(
        Counts[NameValue] for NameValue in ("body", "face", "edge", "vertex")
    ) == (
        1,
        3,
        2,
        2,
    )
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
            Vertex = RequireAsm(Table, ReadAsmPtr(Record, 3), "vertex", 6)
            assert ReadAsmPtr(Record, 3) == ReadAsmPtr(Record, 5)
            Point = RequireAsm(Table, ReadAsmPtr(Vertex, 5), "point", 4)
            Curve = RequireAsm(Table, ReadAsmPtr(Record, 8), "ellipse-curve", 9)
            Center = ReadAsmVec(Curve, 3, 19)
            Radius = ReadAsmVec(Curve, 5, 20).x
            Start = ReadAsmNum(Record, 4)
            Actual = ReadAsmVec(Point, 3, 19)
            assert (Actual.x, Actual.y, Actual.z) == Approx(
                (
                    Center.x + Radius * Cosine(Start),
                    Center.y + Radius * SineValue(Start),
                    Center.z,
                )
            )
