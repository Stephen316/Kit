from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue, TextValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.adapters.Fusion.Native.Rectangle.RectSketchProof import RectSketchProof
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.Transform import KAxisZ, KTransformIdentity, Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordTopology import TopologyCounts


# the project sketch contract needs a shared interpretation so public document claims remain grounded in native records
def ProjectSketch(
    Context: ExtrudeContext,
    Shape: RectGeometry,
    Rectangle: RectSketchProof | None = None,
) -> Sketch:
    return Sketch(
        Context.Sketch.Identity,
        TextValue(Context.Sketch.Fields["userName"]),
        Context.Plane.Identity,
        Shape.Entities,
        constraints=Rectangle.Relations if Rectangle else (),
        parameter_ids=RectParamIds(Rectangle),
        closed_profile_entity_ids=(
            tuple(NodeValue.Identity for NodeValue in Shape.LineNodes),
        ),
    )


# the project features contract needs a shared interpretation so public document claims remain grounded in native records
def ProjectFeatures(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Rectangle: RectSketchProof | None = None,
    Direction: SpaceVector = KAxisZ,
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
        parameter_ids=RectParamIds(Rectangle),
    )
    Definition = DistanceExtrude(
        Along.Identity, Direction, TaperParameterId=Taper.Identity
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


# the sketch and its history feature share the same verified owned parameters
def RectParamIds(Rectangle: RectSketchProof | None) -> tuple[str, ...]:
    return (
        tuple(NodeValue.Identity for NodeValue in Rectangle.Parameters)
        if Rectangle
        else ()
    )


# the project body contract needs a shared interpretation so public document claims remain grounded in native records
def ProjectBody(
    Context: ExtrudeContext,
    Shape: RectGeometry,
    MaterialId: str,
    DepthSpan: tuple[float, float] | None = None,
    FrameValue: Transform = KTransformIdentity,
) -> tuple[BrepModel, DesignBody]:
    Height = NumberValue(Context.Along.Fields["value"]) * 10
    Lower, Upper = DepthSpan if DepthSpan is not None else (0.0, Height)
    Geometry, Volume, AreaValue, Bounds = BuildPrism(
        Context.BodyNode.Identity, FrameValue, Shape.Lines, Lower, Upper
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
