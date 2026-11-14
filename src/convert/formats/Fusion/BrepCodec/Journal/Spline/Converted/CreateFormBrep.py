from dataclasses import dataclass as MakeDataClass
from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.MakePolyStates import (
    MakePolyStates,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.CheckGeometry import (
    CheckGeometry,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.CheckFormBody import (
    CheckFormBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormMarks import (
    FormMarks,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.MakeFormNodes import (
    MakeFormNodes,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.OrderFormNodes import (
    OrderFormNodes,
)
from convert.formats.Fusion.BrepCodec.Journal.States.StreamState import StreamState
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface

KHistoryHeader = BrepHeader(23200, 2, 3, 50.0, 1e-6, 1e-10)
KSnapshotHeader = BrepHeader(23200, 2, 2, 10.0, 1e-6, 1e-10)
KFormHistory = HistoryState(4, 2, 4, 1, 2)


@MakeDataClass(frozen=True, slots=True)
class FormBrep:
    History: JournalModel
    Snapshot: GeometryState


def CheckFormMarks(Marks: FormMarks) -> None:
    if not isinstance(CastValue(object, Marks), FormMarks):
        raise ValueError("Converted Form BRep needs typed provenance marks")
    if not isinstance(CastValue(object, Marks.Stamp), GeometryStamp):
        raise ValueError("Converted Form BRep needs a geometry stamp")
    for Number in (Marks.UnixMicros, Marks.FeatureId):
        if type(Number) is not int or not 0 <= Number < 1 << 53:
            raise ValueError("Converted Form BRep marks must be exact integers")


def CreateFormBrep(
    Surface: TsplineSurface, Model: FormBody, Marks: FormMarks
) -> FormBrep:
    CheckFormBody(Model, Surface)
    CheckFormMarks(Marks)
    Entities = OrderFormNodes(MakeFormNodes(Surface, Model, Marks, True))
    Stream = StreamState(4, 4, 0, KFormHistory.NextEntityTag, -1, 0, 1, -1)
    History = JournalModel(
        KHistoryHeader,
        Marks.Stamp,
        len(Entities),
        Entities,
        Stream,
        MakePolyStates(KFormHistory, len(Entities)),
    )
    _ = Materialize(History)
    Snapshot = GeometryState(
        KSnapshotHeader,
        Marks.Stamp,
        OrderFormNodes(MakeFormNodes(Surface, Model, Marks, False)),
    )
    CheckGeometry(Snapshot)
    return FormBrep(History, Snapshot)
