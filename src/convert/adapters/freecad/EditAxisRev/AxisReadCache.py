from collections.abc import Mapping
from dataclasses import replace as Replace
from zipfile import ZipFile, ZipInfo

from convert.adapters.freecad.EditAxisRev.AxisRevPlan import AxisRevPlan
from convert.adapters.freecad.EditAxisRev.AxisReadGraph import AxisGraph
from convert.adapters.freecad.EditRead.Sketch.SavedSketchFiles import ReadShapeFile
from convert.adapters.freecad.EditRead.Sketch.SketchEvidence import (
    CheckCarriers,
    CheckEmptyFile,
)
from convert.adapters.freecad.EditRev.RevCacheProof import CheckRevWire
from convert.adapters.freecad.EditShape.SavedSketchWire import (
    IsSketchCache,
    KMaxSketchBytes,
)
from convert.adapters.freecad.Native import NativeObject
from convert.adapters.freecad.ReconcileEdit import ReadEditBrep
from interchange.geometry.models.GeometryCurves import PointGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity


# cache ownership distinguishes live sketch geometry from optional native naming data
def ReadAxisCache(Native: NativeObject, Field: str) -> str:
    Entry = ReadShapeFile(Native, Field)
    if Entry and Entry != f"{Native.name}.{Field}.brp":
        raise ValueError("FreeCAD editable sketch axis native shape ownership changed")
    for NodeValue in Native.properties[Field][1:]:
        NameValue = NodeValue.get("file")
        if NameValue is not None and (
            NodeValue.tag != "ElementMap2"
            or NameValue != f"{Native.name}.{Field}.Map.txt"
        ):
            raise ValueError(
                "FreeCAD editable sketch axis native shape map ownership changed"
            )
    return Entry or ""


# the persistent edge name can resolve only to the exact derived guide index
def CheckAxisMap(
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    Native: NativeObject,
    SketchValue: Sketch,
) -> None:
    Shape = Native.properties["Shape"]
    NameValue = f"{Native.name}.Shape.Map.txt"
    Mappings = Shape.findall("./ElementMap2")
    if (
        len(Mappings) != 1
        or Mappings[0].attrib != {"file": NameValue}
        or len(Mappings[0])
    ):
        raise ValueError("FreeCAD editable sketch axis guide map is missing")
    Tokens = ReadEditBrep(
        Archive, Members, NameValue, 4096, "editable sketch axis map"
    ).split()
    GuideId = len(SketchValue.entities) + 1
    PointIds = tuple(
        Index
        for Index, Value in enumerate(SketchValue.entities, 1)
        if isinstance(Value.geometry, PointGeometry)
    )
    VertexIds = (
        f"g{GuideId}v1",
        f"g{GuideId}v2",
        *(f"g{Index}v1" for Index in PointIds),
    )
    MapId = Tokens[2] if len(Tokens) > 2 else b""
    EdgeValue = f";g{GuideId}.3 0".encode()
    Vertices = [f";{Identity}.3 0".encode() for Identity in VertexIds]
    if (
        not MapId.isdigit()
        or Tokens
        != (
            b"BeginElementMap v1 "
            + MapId
            + b" PostfixCount 3 Edge Vertex ;SKT MapCount 1 ElementMap 1 "
            + MapId
            + b" 2 Edge ChildCount 0 NameCount 2 0 "
            + EdgeValue
            + f" Vertex ChildCount 0 NameCount {len(Vertices) + 1} 0 ".encode()
            + b" ".join(Vertices)
            + b" EndMap"
        ).split()
    ):
        raise ValueError("FreeCAD editable sketch axis guide map changed")


# both native caches must confirm their sketch controls before a saved edit can be used
def CheckAxisCaches(
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    Graph: AxisGraph,
    PlanValue: AxisRevPlan,
    Original: Sketch,
    Profile: Sketch,
    AxisSketch: Sketch,
    Guide: SketchEntity,
) -> tuple[str, bool]:
    CheckCarriers(Graph.Objects, Members)
    ShapeEntry = ReadAxisCache(Graph.Feature, "Shape")
    ProfileEntry = ReadAxisCache(Graph.Profile, "Shape")
    AxisEntry = ReadAxisCache(Graph.AxisSketch, "Shape")
    for Native in (Graph.Profile, Graph.AxisSketch):
        CheckEmptyFile(Members, ReadAxisCache(Native, "InternalShape"))
    if not ShapeEntry or bool(ProfileEntry) != bool(AxisEntry):
        raise ValueError("FreeCAD editable sketch axis native caches are incomplete")
    CheckRevWire(
        Archive, Members, ProfileEntry, (), Original, Profile, PlanValue.ProfileFrame
    )
    IsSeed = not AxisEntry
    if IsSeed:
        if not all(
            Value.touched for Value in (Graph.Feature, Graph.Profile, Graph.AxisSketch)
        ):
            raise ValueError("FreeCAD editable sketch axis seed state changed")
        return ShapeEntry, True
    if any(Value.touched for Value in (Graph.Feature, Graph.Profile, Graph.AxisSketch)):
        raise ValueError("FreeCAD editable sketch axis rebuild is pending")
    CheckAxisMap(Archive, Members, Graph.AxisSketch, AxisSketch)
    AxisData = ReadEditBrep(
        Archive, Members, AxisEntry, KMaxSketchBytes, "editable sketch axis"
    )
    AxisWire = Replace(AxisSketch, entities=(*AxisSketch.entities, Guide))
    if not IsSketchCache(AxisData, AxisWire, PlanValue.AxisFrame, DirectedLines=True):
        raise ValueError(
            "FreeCAD editable sketch axis cache disagrees with its geometry"
        )
    return ShapeEntry, False
