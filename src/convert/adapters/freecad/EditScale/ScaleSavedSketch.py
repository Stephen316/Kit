from collections.abc import Mapping

from convert.adapters.freecad.EditRead.Sketch.SavedSketchGeom import ReadSketchGeom
from convert.adapters.freecad.EditRead.Sketch.SavedSketchRules import CheckSavedRules
from convert.adapters.freecad.EditRead.Sketch.SketchParams import KeepSketchRef
from convert.adapters.freecad.EditRing.RingChange import SyncRingEdit
from convert.adapters.freecad.EditScale.ScaleWritePlan import ScaleWritePlan
from convert.adapters.freecad.EditShape.SavedSketchWire import IsSketchCache
from convert.adapters.freecad.Native import NativeObject
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.Sketch import Sketch


# standalone datum sketches can change only the point explicitly consumed by the scale
def CheckScaleEdit(Original: Sketch, Edited: Sketch, PointId: str) -> None:
    if any(
        Before is not After and Before.id != PointId
        for Before, After in zip(Original.entities, Edited.entities, strict=True)
    ):
        raise ValueError("FreeCAD editable Scale has an unrelated sketch geometry edit")


# solved sketch entries and independent wire caches must corroborate each retained edit
def ReadScaleRings(
    Document: CadDocument,
    PlanValue: ScaleWritePlan,
    SketchObjs: Mapping[str, NativeObject],
    Originals: Mapping[str, NativeObject],
    Shapes: Mapping[str, bytes],
) -> tuple[Sketch, ...]:
    Profiles = {BodyValue.SketchId for BodyValue in PlanValue.Bodies}
    Frames = {Value.id: Value.transform for Value in Document.support_planes}
    Params = {Value.id: Value for Value in Document.parameters}
    Result: list[Sketch] = []
    for Original in Document.sketches:
        Native = SketchObjs[Original.id]
        Edited = ReadSketchGeom(Native, Original)
        PointId = (
            PlanValue.Center.PointId if Original.id == PlanValue.Center.SketchId else ""
        )
        if Original.id in Profiles:
            Edited = SyncRingEdit(Original, Edited, ExtraPointId=PointId)
        else:
            CheckScaleEdit(Original, Edited, PointId)
        if Original.constraints:
            Measures = CheckSavedRules(
                Native,
                Originals[Native.name].properties["Constraints"],
                Original,
                Edited,
                Params,
            )
            if any(
                KeepSketchRef(Params[Identity], Value) is not Params[Identity]
                for Identity, Value in Measures.items()
            ):
                raise ValueError(
                    "FreeCAD editable Scale sketch reference value changed"
                )
        if not IsSketchCache(
            Shapes.get(Native.name, b""),
            Edited,
            Frames[Original.support_plane_id],
            ClosedWire=bool(Edited.closed_profile_entity_ids),
        ):
            raise ValueError(
                "FreeCAD editable Scale sketch cache disagrees with its geometry"
            )
        Result.append(Edited)
    return tuple(Result)
