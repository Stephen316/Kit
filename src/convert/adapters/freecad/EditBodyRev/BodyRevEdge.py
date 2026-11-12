from collections.abc import Mapping
from math import isfinite as IsFinite
from uuid import UUID as ParseUuid
from typing import cast as CastValue

from convert.adapters.base.WriteValidate import IsObjectTuple
from convert.adapters.freecad.EditAxisRev.AxisEndpoints import WorldAxisLine
from convert.adapters.freecad.EditBodyRev.BodyAxisEdit import (
    BodyAxisVector,
    ReadAxisEdit,
    ReadEditedAxis,
)
from convert.formats.Fusion.BodyBlob import KHistoryPrefix, KMaxAsmSize
from convert.formats.Fusion.Extrudes.ExtrudeRead import KExtrudeGuid
from convert.formats.Fusion.SelectionProxy import KSelectProxy
from convert.formats.Fusion.Topology.AsmEdge.AsmPoints import AsmPointMm, IsAsmNear
from convert.formats.Fusion.Topology.AsmEdge.PrismProfile import ReadProfileTags
from convert.formats.Fusion.Topology.BodyAnchor import KAnchorGuid, KBodyGuid
from convert.formats.Fusion.Topology.BodyAsmMap import KAsmName
from convert.formats.Fusion.Topology.BodyCollectionRole import KBodyHistory
from convert.formats.Fusion.Topology.LineContext import KLineContext
from convert.formats.Fusion.Topology.PickDescriptor import KPickHelper, KTopoSelect
from convert.formats.Fusion.Topology.PickSupport import KSupportGuid
from convert.formats.Fusion.Topology.RecipeRead import KRecipeGuid
from interchange.brep.topology.BrepModel import BrepModel
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Selection import SelectPathElem, Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector

# the resolved selection carries these exact ordered native links before its shape witness
KPickSpanKinds = (
    KSelectProxy,
    KTopoSelect,
    KRecipeGuid,
    KLineContext,
    KAnchorGuid,
    KPickHelper,
    KSupportGuid,
    KBodyGuid,
    KExtrudeGuid,
    KBodyHistory,
    "asm_history",
)


# selection identity and typed path must name the exact resolved source body and edge
def ReadBodyPick(
    SelectionValue: Selection,
    FeatureValue: FeatureStep,
    Definition: AngularRevolve,
    SourceBody: DesignBody,
    Creator: FeatureStep,
) -> str:
    SelectId = FeatureValue.attributes.get("fusion.revolve.axis_selection_id")
    Evidence = FeatureValue.attributes.get("fusion.revolve.axis_edge_source")
    Origin = SelectionValue.provenance
    Attrs = SelectionValue.attributes
    Handle = Attrs.get("asm_body_handle")
    if (
        type(SelectId) is not int
        or SelectId <= 0
        or SelectionValue.id != f"fusion-selection-{SelectId}-axis"
        or FeatureValue.selection_ids != (SelectionValue.id,)
        or Definition.AxisSelectionId != SelectionValue.id
        or SelectionValue.query != {"kind": "body_edge"}
        or len(SelectionValue.path) != 2
        or SelectionValue.path[0] != SelectPathElem("body", SourceBody.id)
        or SelectionValue.path[1]
        != SelectPathElem("edge", SelectionValue.path[1].entity_id)
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or Origin.native_id != str(SelectId)
        or not isinstance(Evidence, Mapping)
        or Attrs != {**Evidence, "asm_body_handle": Handle}
        or type(Handle) is not int
        or Handle <= 0
    ):
        raise ValueError("FreeCAD editable body axis Revolve selection disagrees")
    CheckPickOrigin(SelectionValue, FeatureValue, SourceBody, Creator)
    CheckRecipe(Attrs)
    return SelectionValue.path[1].entity_id


# exact provenance ties the creator and native body anchor to the named edge selection
def CheckPickOrigin(
    SelectionValue: Selection,
    FeatureValue: FeatureStep,
    SourceBody: DesignBody,
    Creator: FeatureStep,
) -> None:
    Origin, FeatureOrigin = SelectionValue.provenance, FeatureValue.provenance
    BodyOrigin, CreatorOrigin = SourceBody.provenance, Creator.provenance
    Attrs = SelectionValue.attributes
    if (
        Origin is None
        or FeatureOrigin is None
        or BodyOrigin is None
        or CreatorOrigin is None
    ):
        raise ValueError(
            "FreeCAD editable body axis Revolve selection provenance is missing"
        )
    Spans = Origin.spans
    if (
        tuple(Value.record_kind for Value in Spans) != KPickSpanKinds
        or not all(Value in FeatureOrigin.spans for Value in Spans[:9])
        or Spans[7] != BodyOrigin.spans[0]
        or Spans[4] != BodyOrigin.spans[1]
        or Spans[8] != CreatorOrigin.spans[0]
        or Attrs.get("native_body_id") != int(BodyOrigin.native_id)
        or Attrs.get("native_source_feature_id") != int(CreatorOrigin.native_id)
        or Attrs.get("native_body_anchor_id")
        != SourceBody.attributes.get("fusion.native_body_anchor_id")
        or any(
            type(NativeId := Attrs.get(NameValue)) is not int or NativeId <= 0
            for NameValue in (
                "native_recipe_id",
                "native_line_context_id",
            )
        )
        or not Spans[-1].stream.startswith(KHistoryPrefix)
        or KAsmName.fullmatch(Spans[-1].stream.removeprefix(KHistoryPrefix)) is None
        or Spans[-1].offset != 0
        or not 0 < Spans[-1].length <= KMaxAsmSize
    ):
        raise ValueError(
            "FreeCAD editable body axis Revolve native edge evidence disagrees"
        )


# native identity and the bounded recipe name table must remain present together
def CheckRecipe(Attrs: Mapping[str, object]) -> None:
    for KeyName in ("native_namespace", "native_entity_guid"):
        RawValue = Attrs.get(KeyName)
        if not isinstance(RawValue, str) or str(ParseUuid(RawValue)) != RawValue:
            raise ValueError(
                "FreeCAD editable body axis Revolve native name is unresolved"
            )
    Terms = Attrs.get("recipe_terms")
    if not IsObjectTuple(Terms) or len(Terms) != 4 or len(set(Terms)) != 4:
        raise ValueError("FreeCAD editable body axis Revolve recipe names disagree")


# only the chosen base rim edge can map back to a single authored sketch line
def ReadSeedLine(
    EdgeId: str,
    Model: BrepModel,
    SketchValue: Sketch,
    LineRing: tuple[LineGeometry, ...],
    DepthMm: float,
) -> tuple[str, LineGeometry, SpaceVector, SpaceVector]:
    (Members,) = SketchValue.closed_profile_entity_ids
    Entities = {Value.id: Value for Value in SketchValue.entities}
    CurveTags = ReadProfileTags(tuple(Entities[Identity] for Identity in Members))
    Count = len(CurveTags)
    Offset = Count if DepthMm < 0.0 else 0
    Indices = tuple(
        Index
        for Index, Value in enumerate(Model.edges[Offset : Offset + Count])
        if Value.id == EdgeId
    )
    if len(Indices) != 1:
        raise ValueError(
            "FreeCAD editable body axis Revolve requires the source sketch plane rim edge"
        )
    (Index,) = Indices
    ((Identity, LineValue),) = tuple(
        (Member, Geometry)
        for Member, Geometry in zip(Members, LineRing, strict=True)
        if Entities[Member].attributes.get("fusion.entity_tag") == CurveTags[Index]
    )
    return (
        Identity,
        LineValue,
        Model.vertices[Offset + Index].point,
        Model.vertices[Offset + (Index + 1) % Count].point,
    )


# the source curve tag maps a stable sketch line to the current signed prism cap
def FindSeedEdge(
    LineId: str,
    Model: BrepModel,
    SketchValue: Sketch,
    DepthMm: float,
) -> str:
    (Members,) = SketchValue.closed_profile_entity_ids
    Entities = {Value.id: Value for Value in SketchValue.entities}
    CurveTags = ReadProfileTags(tuple(Entities[Identity] for Identity in Members))
    Index = CurveTags.index(Entities[LineId].attributes["fusion.entity_tag"])
    Offset = len(CurveTags) if DepthMm < 0.0 else 0
    return Model.edges[Offset + Index].id


# the projected line context keeps three finite centimeter coordinates per endpoint
def ReadCachePoint(SelectionValue: Selection, KeyName: str) -> SpaceVector:
    Value = SelectionValue.attributes.get(KeyName)
    if (
        not IsObjectTuple(Value)
        or len(Value) != 3
        or any(
            type(PartValue) is not float or not IsFinite(PartValue)
            for PartValue in Value
        )
    ):
        raise ValueError("FreeCAD editable body axis Revolve line cache is malformed")
    return AsmPointMm(SpaceVector(*CastValue(tuple[float, float, float], Value)))


# the native line cache proves endpoint direction independently of prism winding
def ReadSeedAxis(
    SelectionValue: Selection,
    LineValue: LineGeometry,
    FrameValue: Transform,
    RimStart: SpaceVector,
    RimEnd: SpaceVector,
) -> tuple[SpaceVector, SpaceVector]:
    CachedStart, CachedEnd = (
        ReadCachePoint(SelectionValue, KeyName)
        for KeyName in ("cached_start_cm", "cached_end_cm")
    )
    Start, Finish, _ = WorldAxisLine(LineValue, FrameValue)
    if {Start, Finish} != {RimStart, RimEnd}:
        raise ValueError("FreeCAD editable body axis Revolve source rim disagrees")
    Direct = IsAsmNear(RimStart, CachedStart) and IsAsmNear(RimEnd, CachedEnd)
    Reverse = IsAsmNear(RimEnd, CachedStart) and IsAsmNear(RimStart, CachedEnd)
    if Direct == Reverse:
        raise ValueError(
            "FreeCAD editable body axis Revolve source line cache disagrees"
        )
    return (RimStart, RimEnd) if Direct else (RimEnd, RimStart)


# an edited source line remains bound by native point identities and the current neutral rim
def ReadBoundAxis(
    PickValue: Selection,
    Metadata: Mapping[str, object],
    SketchValue: Sketch,
    Frame: Transform,
    RimData: tuple[str, LineGeometry, SpaceVector, SpaceVector],
    DepthMm: float,
) -> tuple[SpaceVector, SpaceVector]:
    LineId, LineValue, RimStart, RimEnd = RimData
    Binding = ReadAxisEdit(Metadata, PickValue.id)
    if Binding is None:
        if DepthMm < 0.0:
            raise ValueError(
                "FreeCAD editable body axis original source depth must be positive"
            )
        return ReadSeedAxis(PickValue, LineValue, Frame, RimStart, RimEnd)
    _ = BodyAxisVector(
        ReadCachePoint(PickValue, "cached_start_cm"),
        ReadCachePoint(PickValue, "cached_end_cm"),
    )
    Start, Finish = ReadEditedAxis(SketchValue, Frame, Binding)
    if Binding.LineId != LineId or {Start, Finish} != {RimStart, RimEnd}:
        raise ValueError("FreeCAD editable body axis verified source rim disagrees")
    return Start, Finish
