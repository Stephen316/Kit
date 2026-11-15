from dataclasses import replace as Replace

from convert.adapters.solidworks.core.Native import NativeModel
from convert.adapters.solidworks.resolved.RectanglePart import RectanglePart


# the typed history replaces sampled direction and the displayed length after identity joins
def AttachRectBoss(Model: NativeModel, Parsed: RectanglePart) -> NativeModel:
    BossValue = Parsed.Boss
    if BossValue is None:
        return Model
    FeatureKey = BossValue["native_feature_id"], BossValue["name"]
    Owners = tuple(
        ItemValue for ItemValue in Model.operations if (ItemValue.object_id, ItemValue.name) == FeatureKey
    )
    Features = tuple(
        ItemValue for ItemValue in Model.features if (ItemValue.object_id, ItemValue.name) == FeatureKey
    )
    Sketch = Parsed.Profile
    if len(Owners) != 1 or len(Features) != 1 or not any(
        (ItemValue.object_id, ItemValue.name) == (Sketch.FeatureId, Sketch.NameValue)
        for ItemValue in Model.sketches
    ):
        return Model
    (Owner,), (Feature,) = Owners, Features
    if Owner.kind != "join" or Owner.native_stream != Feature.native_stream:
        return Model
    Depth = BossValue["depth_display"]["dimension"]
    EndData = BossValue["end_specification"]
    DepthMm = Depth["metres"] * 1000
    Lengths = tuple(ItemValue for ItemValue in Feature.dimensions if ItemValue.kind == "length")
    if len(Lengths) != 1:
        return Model
    (Length,) = Lengths
    ProfileRef = BossValue["profile_ref_offset"]
    EndStart = EndData["offset"]
    Operation = Replace(
        Owner,
        profile_id=Sketch.FeatureId,
        dependencies=(Sketch.FeatureId,),
        native_offset=BossValue["offset"],
        native_end=BossValue["end"],
        length_mm=DepthMm,
        direction_code=EndData["direction"],
        termination_code=EndData["conditions"][0],
        end_spec_offset=EndStart,
        archive_spans=(
            (ProfileRef, 2, "operation-profile-reference"),
            (EndStart, EndData["depth_dimension_offset"] - EndStart, "extrusion-end-spec"),
            (Depth["value_offset"], 8, "extrusion-depth-scalar"),
        ),
    )
    Authored = Replace(
        Length, value_mm=DepthMm, native_value=Depth["metres"],
        native_offset=Depth["value_offset"],
    )
    Projected = Replace(
        Feature,
        native_offset=BossValue["offset"],
        native_end=BossValue["end"],
        dimensions=tuple(
            Authored if ItemValue is Length else ItemValue for ItemValue in Feature.dimensions
        ),
    )
    return Replace(
        Model,
        operations=tuple(Operation if ItemValue is Owner else ItemValue for ItemValue in Model.operations),
        features=tuple(Projected if ItemValue is Feature else ItemValue for ItemValue in Model.features),
    )
