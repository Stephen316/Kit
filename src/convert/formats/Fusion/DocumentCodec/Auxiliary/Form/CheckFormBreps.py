from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListPrograms import ListPrograms


def CheckFormBreps(Value: DocumentModel, Surfaces: tuple[TsplineSurface, ...]) -> None:
    Tables = tuple(
        BodyValue.History.Entities
        for BodyValue in Value.Bodies
        if isinstance(BodyValue.History, JournalModel)
    ) + tuple(
        SnapValue.Snapshot.Entities
        for SnapValue in Value.Snapshots
        if isinstance(SnapValue.Snapshot, GeometryState)
    )
    for Entities in Tables:
        if any(Program not in Surfaces for Program in ListPrograms(Entities)):
            raise ValueError(
                "Converted Form BRep embeds a T-spline program absent from its parts"
            )
