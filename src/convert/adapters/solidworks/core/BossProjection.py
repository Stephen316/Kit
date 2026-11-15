from dataclasses import replace as Replace

from convert.adapters.solidworks.core.Native import NativeModel
from convert.adapters.solidworks.resolved.RectanglePart import RectanglePart


# the typed history replaces sampled direction and XML display length after identity joins
def AttachRectBoss(Model: NativeModel, Parsed: RectanglePart) -> NativeModel:
    Boss = Parsed.Boss
    if Boss is None:
        return Model
    Key = Boss["native_feature_id"], Boss["name"]
    Owners = tuple(
        Item for Item in Model.operations if (Item.object_id, Item.name) == Key
    )
    Features = tuple(
        Item for Item in Model.features if (Item.object_id, Item.name) == Key
    )
    Sketch = Parsed.Profile
    if len(Owners) != 1 or len(Features) != 1 or not any(
        (Item.object_id, Item.name) == (Sketch.FeatureId, Sketch.NameValue)
        for Item in Model.sketches
    ):
        return Model
    (Owner,), (Feature,) = Owners, Features
    if Owner.kind != "join" or Owner.native_stream != Feature.native_stream:
        return Model
    Depth = Boss["depth_display"]["dimension"]
    End = Boss["end_specification"]
    DepthMm = Depth["metres"] * 1000
    Lengths = tuple(Item for Item in Feature.dimensions if Item.kind == "length")
    if len(Lengths) != 1:
        return Model
    (Length,) = Lengths
    ProfileRef = Boss["profile_ref_offset"]
    EndStart = End["offset"]
    Operation = Replace(
        Owner,
        profile_id=Sketch.FeatureId,
        dependencies=(Sketch.FeatureId,),
        native_offset=Boss["offset"],
        native_end=Boss["end"],
        length_mm=DepthMm,
        direction_code=End["direction"],
        termination_code=End["conditions"][0],
        end_spec_offset=EndStart,
        archive_spans=(
            (ProfileRef, 2, "operation-profile-reference"),
            (EndStart, End["depth_dimension_offset"] - EndStart, "extrusion-end-spec"),
            (Depth["value_offset"], 8, "extrusion-depth-scalar"),
        ),
    )
    Authored = Replace(
        Length, value_mm=DepthMm, native_value=Depth["metres"],
        native_offset=Depth["value_offset"],
    )
    Projected = Replace(
        Feature,
        native_offset=Boss["offset"],
        native_end=Boss["end"],
        dimensions=tuple(
            Authored if Item is Length else Item for Item in Feature.dimensions
        ),
    )
    return Replace(
        Model,
        operations=tuple(Operation if Item is Owner else Item for Item in Model.operations),
        features=tuple(Projected if Item is Feature else Item for Item in Model.features),
    )
