from convert.adapters.Fusion.Authoring.MakeFeatures import MakeFeatures
from convert.adapters.Fusion.Authoring.MakeGeometry import MakeGeometry
from convert.adapters.Fusion.Authoring.MakeParams import MakeParams
from convert.adapters.Fusion.Authoring.MakePartBody import MakePartBody
from convert.adapters.Fusion.Authoring.MakePartParams import MakePartParams
from convert.adapters.Fusion.Authoring.MakeSketch import MakeSketch
from convert.adapters.Fusion.Authoring.ProfileShape import HasSolid
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.formats.Fusion.DocumentCodec.CheckDocSpec import CheckDocSpec
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.materials.MaterialRecord import MaterialRecord
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordSource import CadSource


def MakeFusionDoc(SpecValue: DocumentSpec) -> CadDocument:
    CheckDocSpec(SpecValue)
    Geometry, BodyValue = (
        MakeGeometry(SpecValue) if HasSolid(SpecValue) else (None, None)
    )
    if SpecValue.Features:
        Geometry, BodyValue = None, MakePartBody(SpecValue)
    HasSketch = SpecValue.ProfileKind != "parameter"
    Color = SpecValue.Material.Color
    Materials = (
        ()
        if BodyValue is None
        else (
            MaterialRecord(
                "material",
                SpecValue.Material.NameValue,
                SpecValue.Material.Density,
                (Color.RedValue, Color.GreenValue, Color.BlueValue, Color.AlphaValue),
            ),
        )
    )
    return CadDocument(
        CadSource("fusion.f3d", "", ""),
        (Configuration("default", SpecValue.Title, True),),
        MakeParams(SpecValue) + MakePartParams(SpecValue),
        (SupportPlane("plane", "XY", Transform()),) if HasSketch else (),
        (MakeSketch(SpecValue),) if HasSketch else (),
        (),
        MakeFeatures(SpecValue),
        () if BodyValue is None else (BodyValue,),
        brep=Geometry,
        materials=Materials,
        metadata={"fusion.authoring": {"version": 1, "spec": EncodeState(SpecValue)}},
    )
