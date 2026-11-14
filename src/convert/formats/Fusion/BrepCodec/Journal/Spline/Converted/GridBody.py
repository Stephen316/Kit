from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NegateCurve import (
    NegateCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridResult import (
    GridResult,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormEdge,
    FormFace,
    FormSurface,
    FormUse,
    FormWindow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell


def LineTrace(Start: tuple[float, float], Final: tuple[float, float]) -> BsCurve:
    SpanWidth = abs(Final[0] - Start[0]) + abs(Final[1] - Start[1])
    return BsCurve(False, 1, 0, (0.0, SpanWidth), (1, 1), 2, (Start, Final), ())


def SideTraces(Result: GridResult) -> tuple[BsCurve, BsCurve, BsCurve, BsCurve]:
    WidthU = Result.Surface.KnotsU[-1].Value
    HeightV = Result.Surface.KnotsV[-1].Value
    return (
        LineTrace((0.0, 0.0), (WidthU, 0.0)),
        LineTrace((WidthU, 0.0), (WidthU, HeightV)),
        NegateCurve(LineTrace((0.0, HeightV), (WidthU, HeightV))),
        NegateCurve(LineTrace((0.0, 0.0), (0.0, HeightV))),
    )


def SideWindow(CellValue: PatchCell, SideIndex: int) -> FormWindow:
    SpanU = float(CellValue.Window[1])
    SpanV = float(CellValue.Window[3])
    Boxes = (
        (0.0, SpanU, 0.0, 0.0),
        (SpanU, SpanU, 0.0, SpanV),
        (0.0, SpanU, SpanV, SpanV),
        (0.0, 0.0, 0.0, SpanV),
    )
    return FormWindow(CellValue.Face, *Boxes[SideIndex])


def SideWindows(Cells: tuple[PatchCell, ...]) -> tuple[tuple[FormWindow, ...], ...]:
    LastRow = max(-CellValue.Offset[0] for CellValue in Cells)
    LastColumn = max(-CellValue.Offset[1] for CellValue in Cells)
    Places = ((0, 0), (1, -LastColumn), (0, -LastRow), (1, 0))
    Ordered = sorted(Cells, key=lambda CellValue: CellValue.Face)
    return tuple(
        tuple(
            SideWindow(CellValue, SideIndex)
            for CellValue in Ordered
            if CellValue.Offset[Column] == Target
        )
        for SideIndex, (Column, Target) in enumerate(Places)
    )


def GridBody(Result: GridResult) -> FormBody:
    Windows = SideWindows(Result.Patches)
    Edges = tuple(
        FormEdge(
            SideIndex,
            (SideIndex + 1) % 4,
            Result.Bounds[SideIndex],
            ((), (), Result.BoundJumps[SideIndex]),
            "unknown",
            str(SideIndex + 2),
            Windows[SideIndex],
        )
        for SideIndex in range(4)
    )
    SideUses = tuple(
        FormUse(SideIndex, False, Trace)
        for SideIndex, Trace in enumerate(SideTraces(Result))
    )
    Surface = FormSurface(Result.Surface, Result.SurfaceJumps, 0)
    return FormBody(
        Result.Corners,
        Edges,
        (FormFace(Surface, SideUses, "1", True, False),),
        (Result.Patches,),
    )
