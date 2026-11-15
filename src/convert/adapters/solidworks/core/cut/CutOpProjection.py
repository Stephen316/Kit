from dataclasses import replace as Replace

from convert.adapters.solidworks.core.Native import NativeDimension, NativeModel, NativeOperation
from convert.adapters.solidworks.resolved.cut.CutOpRead import CutOperation
from convert.adapters.solidworks.resolved.cut.CutProof import CutProof


# an authored cut depth updates its existing named parameter only when the identity matches
def EditCutDepth(
    Dimensions: tuple[NativeDimension, ...], Saved: CutOperation
) -> tuple[NativeDimension, ...] | None:
    Display = Saved["end_specification"]["depth_display"]
    if Display is None:
        return Dimensions if not any(ItemValue.kind == "length" for ItemValue in Dimensions) else None
    Length = Display["dimension"]
    Matches = tuple(
        ItemValue for ItemValue in Dimensions
        if (ItemValue.name, ItemValue.kind) == (Length["parameter_name"], "length")
    )
    if len(Matches) != 1:
        return None
    (Previous,) = Matches
    Authored = Replace(
        Previous, value_mm=Length["metres"] * 1000,
        native_value=Length["metres"], native_offset=Length["value_offset"],
    )
    return tuple(Authored if ItemValue is Previous else ItemValue for ItemValue in Dimensions)


# the exact result body and end fields replace the sampled operation values
def BuildCutOp(Operation: NativeOperation, Proof: CutProof) -> NativeOperation:
    Saved = Proof.Operation
    EndValue = Saved["end_specification"]
    BodyValue = Saved["solid_body"]
    BossId = Proof.Links.BossValue["native_feature_id"]
    ProfileId = Proof.Links.CutProfile.FeatureId
    Spans: tuple[tuple[int, int, str], ...] = (
        (Saved["profile_ref_offset"], 2, "operation-profile-reference"),
        (BodyValue["offset"], BodyValue["end"] - BodyValue["offset"], "cut-target-body"),
        (EndValue["offset"], EndValue["depth_selector_offset"] - EndValue["offset"], "extrusion-end-spec"),
    )
    Display = EndValue["depth_display"]
    LengthMm = None
    if Display is not None:
        Length = Display["dimension"]
        LengthMm = Length["metres"] * 1000
        Spans += ((Length["value_offset"], 8, "extrusion-depth-scalar"),)
    else:
        Spans += ((EndValue["depth_selector_offset"], 2, "extrusion-depth-absent"),)
    return Replace(
        Operation,
        profile_id=ProfileId, dependencies=(BossId, ProfileId),
        native_offset=Saved["offset"], native_end=EndValue["end"],
        length_mm=LengthMm, direction_code=EndValue["direction"],
        termination_code=EndValue["conditions"][0], end_spec_offset=EndValue["offset"],
        selection_kind="body", selection_offsets=(BodyValue["offset"],),
        selection_references=((BossId, BodyValue["body_id"]),),
        selected_local_ids=(BodyValue["body_id"],), archive_spans=Spans,
    )


# publish the typed operation only when the earlier neutral owners remain unique
def AttachCutOp(Model: NativeModel, Proof: CutProof) -> NativeModel:
    Saved = Proof.Operation
    Identity = Saved["native_feature_id"], Saved["name"]
    Choices = tuple(
        ItemValue for ItemValue in Model.operations
        if (ItemValue.object_id, ItemValue.name, ItemValue.kind) == (*Identity, "cut")
    )
    Features = tuple(
        ItemValue for ItemValue in Model.features
        if (ItemValue.object_id, ItemValue.name) == Identity
    )
    if len(Choices) != 1 or len(Features) != 1:
        return Model
    (Operation,), (Feature,) = Choices, Features
    DimsValue = EditCutDepth(Feature.dimensions, Saved)
    if DimsValue is None:
        return Model
    Projected = BuildCutOp(Operation, Proof)
    Updated = Replace(
        Feature, dimensions=DimsValue, native_offset=Projected.native_offset,
        native_end=Projected.native_end,
    )
    return Replace(
        Model,
        operations=tuple(Projected if ItemValue is Operation else ItemValue for ItemValue in Model.operations),
        features=tuple(Updated if ItemValue is Feature else ItemValue for ItemValue in Model.features),
    )
