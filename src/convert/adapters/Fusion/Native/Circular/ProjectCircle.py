from convert.adapters.Fusion.Native.Graph.GraphValues import TextValue
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.SketchContexts import KSketchContexts
from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.geometry.Extrude.Circular.CircularExtrude import BuildCircular
from interchange.brep.topology.BrepModel import BrepModel
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform
from interchange.records.RecordTopology import TopologyCounts


def CircleSketch(Context: KSketchContexts, Shape: CircleShape) -> Sketch:
    return Sketch(
        Context.Sketch.Identity,
        TextValue(Context.Sketch.Fields["userName"]),
        Context.Plane.Identity,
        Shape.Entities,
        closed_profile_entity_ids=((Shape.CurveNode.Identity,),),
    )


def CircleFeature(Context: KSketchContexts) -> FeatureStep:
    NameValue = TextValue(Context.SketchFeature.Fields["featureUserName"]) or TextValue(
        Context.Sketch.Fields["userName"]
    )
    return FeatureStep(
        Context.SketchFeature.Identity,
        NameValue,
        FeatureKind.KReference,
        0,
        sketch_id=Context.Sketch.Identity,
    )


def CircularBody(
    Context: ExtrudeContext, Shape: CircleShape, Model: FrustumBody, MaterialId: str
) -> tuple[BrepModel, DesignBody]:
    Geometry, Volume, AreaValue, Bounds = BuildCircular(
        Context.BodyNode.Identity,
        Transform(),
        Shape.Geometry,
        0.0,
        Model.Height,
        Model.BottomRadius,
        Model.TopRadius,
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
