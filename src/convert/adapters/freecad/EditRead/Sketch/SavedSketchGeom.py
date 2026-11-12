from dataclasses import replace as Replace

from convert.adapters.freecad.EditRead.Sketch.SavedEntity import ReadSavedEntity
from convert.adapters.freecad.EditRead.Sketch.SavedExternal import CheckExternal
from convert.adapters.freecad.EditRead.Sketch.SavedIncidence import CheckIncidence
from convert.adapters.freecad.EditRead.XmlField import EditChild
from convert.adapters.freecad.Native import NativeObject
from interchange.geometry.models.Sketch import Sketch


# native sketch edits retain original entity ids and their exact incidence roles
def ReadSketchGeom(
    Native: NativeObject, Original: Sketch, TrailingCount: int = 0
) -> Sketch:
    if Native.type_id != "Sketcher::SketchObject":
        raise ValueError("FreeCAD saved sketch object has the wrong type")
    Geometries = EditChild(
        Native, "Geometry", "Part::PropertyGeometryList", "GeometryList"
    )
    Count = len(Original.entities) + TrailingCount
    if Geometries.attrib != {"count": str(Count)} or len(Geometries) != Count:
        raise ValueError("FreeCAD saved sketch geometry count changed")
    CheckExternal(Native)
    ClosedIds = {
        Identity
        for Profile in Original.closed_profile_entity_ids
        for Identity in Profile
    }
    Entities = tuple(
        ReadSavedEntity(
            NodeValue,
            Entity,
            str(Index),
            Entity.construction or (bool(ClosedIds) and Entity.id not in ClosedIds),
        )
        for Index, (NodeValue, Entity) in enumerate(
            zip(Geometries[: len(Original.entities)], Original.entities, strict=True), 1
        )
    )
    if Original.provenance is not None and Original.provenance.adapter == "fusion.f3d":
        CheckIncidence(Entities)
    if all(
        After is Before
        for Before, After in zip(Original.entities, Entities, strict=True)
    ):
        return Original
    return Replace(Original, entities=Entities)
