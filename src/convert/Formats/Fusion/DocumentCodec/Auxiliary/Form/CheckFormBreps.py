from convert.Formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.ListPrograms import ListPrograms


# invalid form breps input must fail here so supporting records retain their owning document relationships
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
