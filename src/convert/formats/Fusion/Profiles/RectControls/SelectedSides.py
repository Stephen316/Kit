from collections import Counter
from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.Profiles.ProfileLoop import ReadProfileLoop
from convert.formats.Fusion.Profiles.ProfileRef import (
    KLoopGuid,
    KProfileGuid,
    ReadProfileRef,
)
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Sketches.LinePointIds import ReadLineEnds
from convert.formats.Fusion.Sketches.SketchRuleScope import (
    IndexRuleEnts,
    ReadSketchRoot,
)
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity


# native endpoints keep this side distinct from a geometrically coincident helper
@MakeDataClass(frozen=True, slots=True)
class SelectedSide:
    Entity: SketchEntity
    StartId: int
    FinishId: int


# the exact authored contour must close by identities independently of member order
def ReadRectSides(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SketchValue: Sketch,
    Feature: FeatureStep,
) -> tuple[int, tuple[SelectedSide, ...]]:
    RootSpan = ReadSketchRoot(SketchValue, Owners)
    DescriptorId = Feature.attributes.get("fusion.profile_descriptor_id")
    ProxyId = Feature.attributes.get("fusion.profile_selection_proxy_id")
    if type(DescriptorId) is not int or type(ProxyId) is not int:
        raise ValueError("Fusion rectangle requires a witnessed selected profile")
    Descriptor = SelectCursor(BulkData, Owners, DescriptorId, KProfileGuid)
    SketchId, LoopId = ReadProfileRef(Descriptor.DataValue)
    if SketchId != RootSpan.ObjectId:
        raise ValueError("Fusion rectangle profile belongs to another sketch")
    LoopValue = SelectCursor(BulkData, Owners, LoopId, KLoopGuid)
    Members, Directions = ReadProfileLoop(
        LoopValue.DataValue, DescriptorId, SketchValue
    )
    NativeOrder = tuple(Entity.id for Entity in Members)
    if (
        len(Members) != 4
        or NativeOrder != Feature.attributes.get("fusion.profile_native_members")
        or Directions != Feature.attributes.get("fusion.profile_native_directions")
        or len(SketchValue.closed_profile_entity_ids) != 1
        or frozenset(NativeOrder) != frozenset(SketchValue.closed_profile_entity_ids[0])
    ):
        raise ValueError("Fusion rectangle selected loop membership disagrees")
    return LoopId, ReadRectEnds(BulkData, Owners, SketchValue, SketchId, Members)


# both profile and sketch only contours need the same owned native endpoint cycle
def ReadRectEnds(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SketchValue: Sketch,
    SketchId: int,
    Members: tuple[SketchEntity, ...],
) -> tuple[SelectedSide, ...]:
    Entities = IndexRuleEnts(BulkData, Owners, SketchValue, SketchId)
    Owned = {Value.id for Value in Entities.values()}
    Sides = tuple(SelectedSide(Entity, *ReadLineEnds(Entity)) for Entity in Members)
    Points = Counter(
        Identity
        for SideValue in Sides
        for Identity in (SideValue.StartId, SideValue.FinishId)
    )
    if (
        len(Sides) != 4
        or any(Value.Entity.id not in Owned for Value in Sides)
        or len(Points) != 4
        or any(Count != 2 for Count in Points.values())
        or len(
            {frozenset((SideValue.StartId, SideValue.FinishId)) for SideValue in Sides}
        )
        != 4
        or any(
            Identity not in Entities
            or not isinstance(Entities[Identity].geometry, PointGeometry)
            for Identity in Points
        )
        or any(
            Entity.attributes.get("fusion.entity_genesis") != 2
            or Entity.construction
            or not isinstance(Entity.geometry, LineGeometry)
            for Entity in Members
        )
    ):
        raise ValueError(
            "Fusion rectangle has no complete authored point identity cycle"
        )
    return Sides
