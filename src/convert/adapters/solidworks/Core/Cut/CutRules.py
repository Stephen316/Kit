from dataclasses import replace as Replace

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.Cut.CutAxes import ProjectCutAxes
from convert.adapters.solidworks.Core.Cut.CutDimRoles import (
    CheckCutParam,
    CheckRolePairs,
    KeepCutScalar,
    ReadCutRoles,
)
from convert.adapters.solidworks.Core.Cut.CutDistances import BuildCutDist
from convert.adapters.solidworks.Core.Cut.CutOrigin import (
    CutOriginCoord,
    CutOriginPoint,
    MakeCutOrigin,
    ReadCutOrigin,
)
from convert.adapters.solidworks.Core.Cut.CutOwners import FindCutOwner
from convert.adapters.solidworks.Core.Cut.CutPerimeter import KCutLoopSource
from convert.adapters.solidworks.Core.Cut.CutRuleLines import MatchRuleLines
from convert.adapters.solidworks.Core.Cut.CutRuleSource import CutRuleSource
from convert.adapters.solidworks.Core.Cut.FaceProjection import KFaceSupportSource
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch, SketchRelation
from interchange.Records.RecordParameter import Parameter


# constraint operands are usable only on the placed cut from this exact configuration sketch
def BindRuleOrigin(
    Document: CadDocument,
    SketchValue: Sketch,
    StepValue: FeatureStep,
    Source: CutRuleSource,
) -> CutOriginPoint:
    RequireArch(
        (
            SketchValue.attributes.get("native_geometry_source"),
            SketchValue.attributes.get("support_plane_source"),
        ),
        (KCutLoopSource, KFaceSupportSource),
        "typed cut perimeter and support available",
    )
    RequireArch(
        SketchValue.attributes.get("native_sketch_object_id"),
        Source.SketchData.Geometry["object_index"],
        "same configuration sketch owner",
    )
    Frames = [
        Value
        for Value in Document.support_planes
        if Value.id == SketchValue.support_plane_id
    ]
    RequireArch(len(Frames), 1, "unique typed cut constraint frame")
    Reference, Owner = ReadCutOrigin(Document, StepValue, Source)
    Coordinates = CutOriginCoord(Reference, Frames[0].transform, Source)
    Origin = MakeCutOrigin(SketchValue, Reference, Owner, Coordinates, Source)
    RequireArch(
        any(Value.id == Origin.Entity.id for Value in SketchValue.entities),
        False,
        "unused cut point identity",
    )
    RequireArch(
        any(Value.id == Origin.PickValue.id for Value in Document.selections),
        False,
        "unused cut origin selection identity",
    )
    return Origin


# every established parameter and relation identity must bind exactly once before replacement
def BindCutRules(
    Document: CadDocument,
    SketchValue: Sketch,
    StepValue: FeatureStep,
    Origin: CutOriginPoint,
    Source: CutRuleSource,
) -> tuple[tuple[SketchRelation, ...], dict[str, Parameter]]:
    Lines = MatchRuleLines(SketchValue, Source)
    Roles = ReadCutRoles(Source)
    CheckRolePairs(Roles, Origin.PointId)
    Owned = [
        Value for Value in Document.parameters if Value.id in SketchValue.parameter_ids
    ]
    Parameters = {Value.id: Value for Value in Owned}
    RequireArch(
        (len(Owned), len(Parameters), len(SketchValue.constraints)),
        (4, 4, 4),
        "four existing cut parameter bindings",
    )
    RequireArch(
        {Value.parameter_id for Value in SketchValue.constraints},
        set(Parameters),
        "one rule owns each cut parameter",
    )
    Distances: list[SketchRelation] = []
    Updated: dict[str, Parameter] = {}
    for RuleValue in SketchValue.constraints:
        ParamValue = Parameters[RuleValue.parameter_id or ""]
        RequireArch(ParamValue.owner_id, StepValue.id, "cut rule owns its parameter")
        RoleValue = Roles.pop(ParamValue.name)
        CheckCutParam(ParamValue, RoleValue, Source)
        Distances.append(BuildCutDist(RuleValue, RoleValue, Source, Origin, Lines))
        Updated[ParamValue.id] = KeepCutScalar(
            ParamValue, RoleValue, Source.ConfigStream
        )
    return (*Distances, *ProjectCutAxes(Source, Lines)), Updated


# publishing a resolved origin also records the earlier feature that owns its projection
def FinishCutRules(
    Document: CadDocument,
    SketchValue: Sketch,
    StepValue: FeatureStep,
    Origin: CutOriginPoint,
    Rules: tuple[SketchRelation, ...],
    Parameters: dict[str, Parameter],
) -> CadDocument:
    Revised = Replace(
        SketchValue,
        entities=(*SketchValue.entities, Origin.Entity),
        constraints=Rules,
        attributes=FreezeMapping(
            {**SketchValue.attributes, "native_constraint_source": KCutLoopSource}
        ),
    )
    Dependencies = tuple(dict.fromkeys((*StepValue.input_feature_ids, Origin.OwnerId)))
    Profile = Replace(
        StepValue,
        input_feature_ids=Dependencies,
        selection_ids=(*StepValue.selection_ids, Origin.PickValue.id),
    )
    return Replace(
        Document,
        sketches=tuple(
            Revised if Value is SketchValue else Value for Value in Document.sketches
        ),
        parameters=tuple(
            Parameters.get(Value.id, Value) for Value in Document.parameters
        ),
        feature_timeline=tuple(
            Profile if Value is StepValue else Value
            for Value in Document.feature_timeline
        ),
        selections=(*Document.selections, Origin.PickValue),
    )


# the complete set of axes dimensions and projected source must succeed as a group
def ProjectCutRules(Document: CadDocument, Source: CutRuleSource) -> CadDocument:
    try:
        SketchValue, StepValue = FindCutOwner(Document, Source.ProfileId)
        Origin = BindRuleOrigin(Document, SketchValue, StepValue, Source)
        Rules, Parameters = BindCutRules(
            Document, SketchValue, StepValue, Origin, Source
        )
    except (KeyError, IndexError, ValueError):
        return Document
    return FinishCutRules(Document, SketchValue, StepValue, Origin, Rules, Parameters)
