from dataclasses import fields as DataFields, is_dataclass as IsDataClass
from typing import cast as CastValue

from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef


def CheckAuxiliary(
    Graph: NativeGraph, Model: DocumentModel, History: PrismHistory
) -> None:
    for PartValue in Model.Snapshots:
        Snapshot = PartValue.Snapshot
        if (
            not isinstance(Snapshot, PrismSnapshot)
            or Snapshot.Model != History.Model
            or Snapshot.TagSet != History.TagSet
        ):
            raise ValueError(
                "Native snapshot geometry or feature identities disagree with history"
            )
        Expected = tuple(
            tuple(Coordinate / 10 for Coordinate in Point)
            for Point in (History.Model.BasePoint,)
        )
        for Region in (Snapshot.Profile, Snapshot.Sketch):
            if len(Region.CornersCm) != 4 or any(
                Point[2] != Expected[0][2] for Point in Region.CornersCm
            ):
                raise ValueError(
                    "Native snapshot sketch is not on the modeled profile plane"
                )
            XValues, YValues = tuple(Point[0] for Point in Region.CornersCm), tuple(
                Point[1] for Point in Region.CornersCm
            )
            SameNumbers(
                (
                    min(XValues) * 10,
                    min(YValues) * 10,
                    (max(XValues) - min(XValues)) * 10,
                    (max(YValues) - min(YValues)) * 10,
                ),
                (
                    *History.Model.BasePoint[:2],
                    History.Model.Width,
                    History.Model.Depth,
                ),
            )
    CheckSceneRefs(Graph, Model.Graphics)


def CheckSceneRefs(Graph: NativeGraph, Value: object) -> None:
    if isinstance(Value, EntityRef):
        if (Value.SegmentId, Value.ObjectId) not in Graph.Nodes:
            raise ValueError(
                "Native display scene references a missing semantic entity"
            )
    elif IsDataClass(Value) and not isinstance(Value, type):
        for Field in DataFields(Value):
            CheckSceneRefs(Graph, getattr(Value, Field.name))
    elif isinstance(Value, tuple):
        for Entry in CastValue(tuple[object, ...], Value):
            CheckSceneRefs(Graph, Entry)
