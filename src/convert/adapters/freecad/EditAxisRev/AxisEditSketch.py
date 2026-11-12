from dataclasses import replace as Replace

from convert.adapters.freecad.EditRead.Sketch.SavedEntity import IsSameCoord
from convert.adapters.freecad.EditRing.RingChange import SyncRingLine
from convert.adapters.freecad.EditRing.RingEndpoints import ReadRingEnds
from interchange.geometry.models.GeometryCurves import PointGeometry
from interchange.geometry.models.Sketch import Sketch


# metadata and unrelated point geometry retain their exact source identities
def CheckAxisEdits(Original: Sketch, Edited: Sketch, Allowed: set[str]) -> None:
    if (
        len(Edited.entities) != len(Original.entities)
        or Replace(Edited, entities=Original.entities) != Original
    ):
        raise ValueError("FreeCAD editable sketch axis sketch identity changed")
    for Before, After in zip(Original.entities, Edited.entities, strict=True):
        if Replace(After, geometry=Before.geometry) != Before:
            raise ValueError("FreeCAD editable sketch axis entity identity changed")
        if (Before.fixed or Before.id not in Allowed) and After != Before:
            raise ValueError("FreeCAD editable sketch axis unrelated geometry changed")


# independently serialized point copies share one value after their exact links agree
def SyncAxisSketch(
    Original: Sketch,
    Edited: Sketch,
    LineIds: tuple[str, ...],
    Pairs: tuple[tuple[str, str], ...] = (),
) -> Sketch:
    Lines = set(LineIds)
    PointIds = {
        Identity
        for Entity in Original.entities
        if Entity.id in Lines
        for Identity in ReadRingEnds(Entity)
    }
    CheckAxisEdits(Original, Edited, Lines | PointIds)
    Points = {
        Entity.id: Entity.geometry.point
        for Entity in Edited.entities
        if Entity.id in PointIds and isinstance(Entity.geometry, PointGeometry)
    }
    if Points.keys() != PointIds:
        raise ValueError("FreeCAD editable sketch axis point records are missing")
    for First, Second in Pairs:
        if not IsSameCoord(Points[First], Points[Second]):
            raise ValueError(
                "FreeCAD editable sketch axis profile corner changed connectivity"
            )
        Points[Second] = Points[First]
    Entities = tuple(
        (
            SyncRingLine(Entity, Points)
            if Entity.id in Lines
            else (
                Replace(Entity, geometry=PointGeometry(Points[Entity.id]))
                if (
                    Entity.id in Points
                    and isinstance(Entity.geometry, PointGeometry)
                    and Entity.geometry.point != Points[Entity.id]
                )
                else Entity
            )
        )
        for Entity in Edited.entities
    )
    Result = Replace(Edited, entities=Entities)
    return Original if Result == Original else Result
