from dataclasses import replace as Replace

from convert.formats.Fusion.Revolves.BuildRevGeom import BuildRevGeom
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform


# angular and plane driven edits regenerate one exact solid with its original identity
def RebuildRevDoc(
    DocValue: CadDocument,
    Profile: Sketch,
    Frame: Transform,
    SpanValue: tuple[float, float],
) -> CadDocument:
    Feature = DocValue.feature_timeline[-1]
    Definition = Feature.definition
    if not isinstance(Definition, (AngularRevolve, PlaneRevolve)):
        raise ValueError("FreeCAD editable Revolve source definition is unavailable")
    (BodyValue,) = DocValue.bodies
    Model, Volume, AreaValue, Bounds = BuildRevGeom(
        BodyValue.id, Feature, Definition, SpanValue, Profile, Frame
    )
    if len(Model.regions) != 1 or Model.validate(frozenset({BodyValue.id})):
        raise ValueError("FreeCAD editable Revolve rebuilt an invalid solid")
    Topology = Replace(
        BodyValue.topology,
        solid_count=len(Model.regions),
        shell_count=len(Model.shells),
        face_count=len(Model.faces),
        edge_count=len(Model.edges),
        vertex_count=len(Model.vertices),
        volume=Volume,
        surface_area=AreaValue,
        bounding_box=Bounds,
        valid=True,
    )
    return Replace(
        DocValue,
        sketches=(Profile,),
        bodies=(Replace(BodyValue, topology=Topology),),
        brep=Model,
    )
