from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue, TextValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordTopology import TopologyCounts


# the project sketch contract needs a shared interpretation so public document claims remain grounded in native records
def ProjectSketch(Context: ExtrudeContext, Shape: RectGeometry) -> Sketch:
    return Sketch(
        Context.Sketch.Identity,
        TextValue(Context.Sketch.Fields["userName"]),
        Context.Plane.Identity,
        Shape.Entities,
        closed_profile_entity_ids=(
            tuple(NodeValue.Identity for NodeValue in Shape.LineNodes),
        ),
    )


# the project features contract needs a shared interpretation so public document claims remain grounded in native records
def ProjectFeatures(
    Graph: NativeGraph, Context: ExtrudeContext
) -> tuple[FeatureStep, ...]:
    Along = Graph.Resolve(Context.Along.Fields["parameter"])
    Taper = Graph.Resolve(Context.Taper.Fields["parameter"])
    SketchName = TextValue(
        Context.SketchFeature.Fields["featureUserName"]
    ) or TextValue(Context.Sketch.Fields["userName"])
    ExtrudeName = TextValue(Context.Extrude.Fields["featureUserName"]) or TextValue(
        Context.Extrude.Fields["featureBaseName"]
    )
    Sketch = FeatureStep(
        Context.SketchFeature.Identity,
        SketchName,
        FeatureKind.KReference,
        0,
        sketch_id=Context.Sketch.Identity,
    )
    Definition = DistanceExtrude(
        Along.Identity, SpaceVector(0.0, 0.0, 1.0), TaperParameterId=Taper.Identity
    )
    Extrude = FeatureStep(
        Context.Extrude.Identity,
        ExtrudeName,
        FeatureKind.KExtrusion,
        1,
        (Sketch.id,),
        Context.Sketch.Identity,
        (Along.Identity, Taper.Identity),
        BooleanOp.KCreate,
        Definition,
    )
    return Sketch, Extrude


# the project body contract needs a shared interpretation so public document claims remain grounded in native records
def ProjectBody(
    Context: ExtrudeContext, Shape: RectGeometry, MaterialId: str
) -> tuple[BrepModel, DesignBody]:
    Height = NumberValue(Context.Along.Fields["value"]) * 10
    Geometry, Volume, AreaValue, Bounds = BuildPrism(
        Context.BodyNode.Identity, Transform(), Shape.Lines, 0.0, Height
    )
    Counts = TopologyCounts(
        1,
        len(Geometry.shells),
        len(Geometry.faces),
        len(Geometry.edges),
        len(Geometry.vertices),
        Volume,
        AreaValue,
        Bounds,
        True,
    )
    BodyValue = DesignBody(
        Context.BodyNode.Identity,
        TextValue(Context.BodyNode.Fields["userName"]),
        Context.Extrude.Identity,
        Counts,
        MaterialId,
        attributes={"creation_index": Context.BodyNode.Fields["creationIndex"]},
    )
    return Geometry, BodyValue
