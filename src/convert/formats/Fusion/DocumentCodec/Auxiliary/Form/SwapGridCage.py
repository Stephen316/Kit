from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.ConvertGrid import (
    ConvertGrid,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridResult import (
    GridResult,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.SwapEntity import (
    SwapEntity,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.CheckFolds import (
    CheckFolds,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.GridBody import GridBody
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


def IsFormBody(Entities: tuple[KJournalEntity, ...]) -> bool:
    return any(
        isinstance(Entity, SplineNode) and isinstance(Entity.Surface, TsplineSurf)
        for Entity in Entities
    )


def SwapAll(
    Entities: tuple[KJournalEntity, ...],
    Prior: GridResult,
    Result: GridResult,
    Surface: TsplineSurface,
) -> tuple[KJournalEntity, ...]:
    return tuple(SwapEntity(Entity, Prior, Result, Surface) for Entity in Entities)


def SwapBody(
    BodyValue: DocumentBody,
    Prior: GridResult,
    Result: GridResult,
    Surface: TsplineSurface,
) -> DocumentBody:
    History = BodyValue.History
    if not isinstance(History, JournalModel) or not IsFormBody(History.Entities):
        return BodyValue
    Entities = SwapAll(History.Entities, Prior, Result, Surface)
    return ReplaceValue(BodyValue, History=ReplaceValue(History, Entities=Entities))


def SwapSnap(
    SnapValue: DocumentSnap,
    Prior: GridResult,
    Result: GridResult,
    Surface: TsplineSurface,
) -> DocumentSnap:
    State = SnapValue.Snapshot
    if not isinstance(State, GeometryState) or not IsFormBody(State.Entities):
        return SnapValue
    Entities = SwapAll(State.Entities, Prior, Result, Surface)
    return ReplaceValue(SnapValue, Snapshot=ReplaceValue(State, Entities=Entities))


def SwapGridCage(Model: DocumentModel, Surface: TsplineSurface) -> DocumentModel:
    if len(Model.Forms) != 1:
        raise ValueError("Fusion grid cage swap needs exactly one Form")
    Prior, Result = ConvertGrid(Model.Forms[0].Surface), ConvertGrid(Surface)
    Layout = (Result.Patches, Result.Surface.KnotsU, Result.Surface.KnotsV)
    if (Prior.Patches, Prior.Surface.KnotsU, Prior.Surface.KnotsV) != Layout:
        raise ValueError("Fusion grid cage swap needs the same grid layout")
    CheckFolds(GridBody(Result))
    if not any(
        isinstance(BodyValue.History, JournalModel)
        and IsFormBody(BodyValue.History.Entities)
        for BodyValue in Model.Bodies
    ):
        raise ValueError("Fusion grid cage swap found no converted Form body")
    Bodies = tuple(
        SwapBody(BodyValue, Prior, Result, Surface) for BodyValue in Model.Bodies
    )
    Snaps = tuple(
        SwapSnap(SnapValue, Prior, Result, Surface) for SnapValue in Model.Snapshots
    )
    Forms = (ReplaceValue(Model.Forms[0], Surface=Surface),)
    return ReplaceValue(
        Model, Bodies=Bodies, Snapshots=Snaps, Forms=Forms, Graphics=None
    )
