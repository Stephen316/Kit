from collections.abc import Mapping

from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch


# local selection targets must travel with the detached component geometry
def GetPickLinks(
    PickValue: Selection, Sketches: Mapping[str, Sketch]
) -> tuple[tuple[str, str], ...]:
    PathElems = PickValue.path
    if (
        not PathElems
        and PickValue.query.get("kind") == "component_origin_axis"
        and PickValue.query.get("axis") in ("X", "Y", "Z")
    ):
        return ()
    Kinds = tuple(Value.entity_kind for Value in PathElems)
    if Kinds == ("support_plane",):
        return (("plane", PathElems[0].entity_id),)
    if Kinds == ("sketch", "sketch_entity"):
        SketchValue = Sketches.get(PathElems[0].entity_id)
        if SketchValue is not None and any(
            Value.id == PathElems[1].entity_id for Value in SketchValue.entities
        ):
            return (("sketch", SketchValue.id),)
    raise ValueError(
        f"Fusion component selection {PickValue.id} has an unresolved local target"
    )
