from dataclasses import dataclass as MakeDataClass
from math import gcd as CommonFactor

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell

KPlace = tuple[int, int, int]
KShift = tuple[int, int]
KSteps = ((1, 0), (0, 1), (-1, 0), (0, -1))


@MakeDataClass(frozen=True, slots=True)
class BlockGrid:
    Faces: tuple[int, ...]
    Places: tuple[KPlace, ...]
    Width: int
    Height: int
    WrapsU: bool
    WrapsV: bool


def NextPlace(
    Graph: CageGraph, Place: KPlace, Corner: int, LinkIndex: int
) -> tuple[int, KPlace]:
    Across = Graph.Links[LinkIndex].Opposite
    Neighbour = Graph.Links[Across].FaceIndex
    Facing = Graph.Loops[Neighbour].index(Across)
    StepU, StepV = KSteps[(Corner + 3 + Place[2]) % 4]
    TurnIndex = (Corner - Facing + Place[2] + 2) % 4
    return Neighbour, (Place[0] + StepU, Place[1] + StepV, TurnIndex)


def SpreadBlock(
    Graph: CageGraph, Faces: tuple[int, ...], Drawn: tuple[bool, ...]
) -> tuple[dict[int, KPlace], list[KShift]]:
    Places: dict[int, KPlace] = {Faces[0]: (0, 0, 0)}
    Shifts: list[KShift] = []
    Queue = [Faces[0]]
    for FaceIndex in Queue:
        for Corner, LinkIndex in enumerate(Graph.Loops[FaceIndex]):
            if Drawn[LinkIndex]:
                continue
            Neighbour, Place = NextPlace(Graph, Places[FaceIndex], Corner, LinkIndex)
            Known = Places.get(Neighbour)
            if Known is None:
                Places[Neighbour] = Place
                Queue.append(Neighbour)
            elif Known[2] != Place[2]:
                raise ValueError("Fusion Form capped layout has a twisted face block")
            else:
                Shifts.append((Place[0] - Known[0], Place[1] - Known[1]))
    return Places, Shifts


def BlockPeriods(Shifts: list[KShift]) -> KShift:
    Leading = (0, 0)
    Trailing = 0
    for Shift in Shifts:
        Current = Shift
        while Current[0] != 0:
            Ratio = Leading[0] // Current[0]
            Leading, Current = Current, (
                Leading[0] - Ratio * Current[0],
                Leading[1] - Ratio * Current[1],
            )
        Trailing = CommonFactor(Trailing, Current[1])
    IsAligned = Leading[1] % Trailing == 0 if Trailing else Leading[1] == 0
    if not IsAligned:
        raise ValueError("Fusion Form capped layout has a sheared periodic block")
    return abs(Leading[0]), Trailing


def AxisValue(Value: int, Lowest: int, Period: int) -> int:
    return Value % Period if Period else Value - Lowest


def PlaceBlock(
    Graph: CageGraph, Faces: tuple[int, ...], Drawn: tuple[bool, ...]
) -> BlockGrid:
    Places, Shifts = SpreadBlock(Graph, Faces, Drawn)
    PeriodU, PeriodV = BlockPeriods(Shifts)
    Columns = [Places[FaceIndex][0] for FaceIndex in Faces]
    RowValues = [Places[FaceIndex][1] for FaceIndex in Faces]
    Cells = tuple(
        (
            AxisValue(Places[FaceIndex][0], min(Columns), PeriodU),
            AxisValue(Places[FaceIndex][1], min(RowValues), PeriodV),
            Places[FaceIndex][2],
        )
        for FaceIndex in Faces
    )
    Width = PeriodU or max(Columns) - min(Columns) + 1
    Height = PeriodV or max(RowValues) - min(RowValues) + 1
    Spots = {(CellValue[0], CellValue[1]) for CellValue in Cells}
    if len(Spots) != len(Faces) or Width * Height != len(Faces):
        raise ValueError("Fusion Form capped layout needs rectangular face blocks")
    return BlockGrid(Faces, Cells, Width, Height, PeriodU > 0, PeriodV > 0)


def ScaledCell(FaceIndex: int, Place: KPlace, Scale: int) -> PatchCell:
    Column, RowIndex, TurnIndex = Place
    Offsets = (
        (-RowIndex, -Column),
        (Column + 1, -RowIndex),
        (RowIndex + 1, Column + 1),
        (-Column, RowIndex + 1),
    )
    First, Second = Offsets[TurnIndex]
    return PatchCell(
        FaceIndex, (0, Scale, 0, Scale), (First * Scale, Second * Scale, TurnIndex)
    )


def GridCells(GridValue: BlockGrid, Scale: int) -> tuple[PatchCell, ...]:
    return tuple(
        ScaledCell(FaceIndex, Place, Scale)
        for FaceIndex, Place in zip(GridValue.Faces, GridValue.Places)
    )
