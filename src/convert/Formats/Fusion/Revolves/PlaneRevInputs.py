from convert.adapters.base.WriteValidate import IsObjectTuple
from convert.Formats.Fusion.Revolves.RevProfile import ReadRevProfile
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane


# only the verified native profile members can supply the bounded meridian
def ProfileLines(
    StepValue: FeatureStep, SketchValue: Sketch
) -> tuple[LineGeometry, ...]:
    Profile = ReadRevProfile(StepValue, SketchValue)
    if not isinstance(Profile, tuple) or len(Profile) != 4:
        raise ValueError("Fusion plane Revolve requires one four-line profile")
    return Profile


# ordered selection roles stay independent of the order of the geometric roots
def TargetPlanes(
    StepValue: FeatureStep,
    Picks: tuple[Selection, ...],
    Frames: dict[str, SupportPlane],
) -> tuple[tuple[Selection, SupportPlane], ...]:
    Identities = StepValue.attributes.get("fusion.revolve.target_selection_ids")
    if not IsObjectTuple(Identities) or len(Identities) not in (1, 2):
        raise ValueError("Fusion plane Revolve requires one or two targets")
    ByIdentity = {Value.id: Value for Value in Picks}
    Targets: list[tuple[Selection, SupportPlane]] = []
    for RoleName, SelectId in zip(("target_one", "target_two"), Identities):
        PickValue = ByIdentity.get(f"fusion-selection-{SelectId}-{RoleName}")
        if PickValue is None or len(PickValue.path) != 1:
            raise ValueError("Missing Fusion plane Revolve target selection")
        (PathValue,) = PickValue.path
        FrameValue = Frames.get(PathValue.entity_id)
        if PathValue.entity_kind != "support_plane" or FrameValue is None:
            raise ValueError("Missing Fusion plane Revolve target frame")
        Targets.append((PickValue, FrameValue))
    return tuple(Targets)
