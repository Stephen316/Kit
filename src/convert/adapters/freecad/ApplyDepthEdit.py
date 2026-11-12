from dataclasses import replace as Replace

from convert.adapters.freecad.ApplyDepthParams import ReadDepthParams
from convert.adapters.freecad.ApplyProfileEdit import GetProfileEdits
from convert.adapters.freecad.EditExtSolid import BuildEditSolid, KEditProfile
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform
from interchange.records.RecordParameter import Parameter


# rebuilding verified geometry keeps the original identities and body measures consistent
def ApplyDepthEdit(
    DocValue: CadDocument,
    ParameterId: str,
    SourceText: str | None,
    DistanceMm: float,
    Profile: KEditProfile,
    FrameValue: Transform,
    ParameterEdits: tuple[Parameter, ...] = (),
    EditedSketch: Sketch | None = None,
) -> CadDocument:
    if not DocValue.feature_timeline or len(DocValue.bodies) != 1:
        raise ValueError("FreeCAD editable extrusion source body is unavailable")
    BodyValue = DocValue.bodies[0]
    ParamValues, DepthMm = ReadDepthParams(
        DocValue.parameters,
        DocValue.feature_timeline[-1],
        ParameterId,
        SourceText,
        DistanceMm,
        ParameterEdits,
    )
    SketchValues = GetProfileEdits(DocValue, Profile, FrameValue, EditedSketch)
    if ParamValues is DocValue.parameters and SketchValues is DocValue.sketches:
        return DocValue
    BrepValue, Volume, AreaValue, Bounds = BuildEditSolid(
        BodyValue.id, FrameValue, Profile, DepthMm
    )
    Topology = Replace(
        BodyValue.topology,
        solid_count=len(BrepValue.regions),
        shell_count=len(BrepValue.shells),
        face_count=len(BrepValue.faces),
        edge_count=len(BrepValue.edges),
        vertex_count=len(BrepValue.vertices),
        volume=Volume,
        surface_area=AreaValue,
        bounding_box=Bounds,
        valid=True,
    )
    return Replace(
        DocValue,
        parameters=ParamValues,
        sketches=SketchValues,
        bodies=(Replace(BodyValue, topology=Topology),),
        brep=BrepValue,
    )
