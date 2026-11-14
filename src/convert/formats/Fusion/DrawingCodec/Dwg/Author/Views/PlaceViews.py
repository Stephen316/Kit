from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.ReadSolid import ReadSolid
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceScale import (
    PlaceScaleMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import SheetSize
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DwgDraft import DwgDraft
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.LinkReactors import (
    LinkReactorsMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.PlaceSource import (
    PlaceSourceMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.PlaceView import (
    PlaceViewMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.PlaceViewAction import (
    KFamily,
    PlaceViewActMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewKeys import ViewKeys
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import Scaled
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewPlan import (
    KUnitScale,
    PlanViews,
    ViewPlan,
)


def RootIndex(Plans: tuple[ViewPlan, ...], Index: int) -> int:
    while Plans[Index].Parent >= 0:
        Index = Plans[Index].Parent
    return Index


def PlaceViewsMut(Ledger: DraftBook, Draft: DwgDraft) -> None:
    if not Draft.Views:
        return
    if Draft.Source is None:
        raise ValueError("Authored DWG views need a view source")
    if Draft.Source.Solid is None:
        raise ValueError("Authored DWG views need the source solid to draw edges")
    Shape = ReadSolid(
        Draft.Source.Solid,
        Scaled(Draft.Source.BoundsMin, KUnitScale),
        Scaled(Draft.Source.BoundsMax, KUnitScale),
    )
    Paper = SheetSize(Draft.Sheet.SheetSize)
    Plans = PlanViews(Draft.Views, Draft.Source, (Paper.PaperWidth, Paper.PaperHeight))
    PlaceSourceMut(Ledger, Draft.Source)
    Placed: list[tuple[ViewKeys, ViewPlan]] = []
    for Planned in Plans:
        ScaleKey = PlaceScaleMut(Ledger, Planned.Frame.ViewScale)
        Placed.append((PlaceViewMut(Ledger, Planned, ScaleKey), Planned))
    for KeySet, Planned in Placed:
        Origin = RootIndex(Plans, Planned.Index)
        Family: KFamily = tuple(
            Member for Member in Placed if RootIndex(Plans, Member[1].Index) == Origin
        )
        PlaceViewActMut(Ledger, KeySet, Planned, Family, Draft.Source, Shape)
    LinkReactorsMut(Ledger)
