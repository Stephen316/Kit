from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.FeatureBoundPlane import BoundDatum
from interchange.features.FeatureStep import FeatureCfgState, FeatureStep
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.records.RecordParameter import Parameter, ParameterValue


# plane only models expose cached geometry when every declared feature becomes inactive
def BuildPlaneHist(RecordKind: str) -> CadDocument:
    Document = MakeFusionDoc(
        DocumentSpec("Plane history", "length", 20.0, ProfileKind="parameter")
    )
    StepValue = FeatureStep(
        "plane",
        "Plane",
        FeatureKind.KReference,
        0,
        parameter_ids=("scalar", "extra"),
        definition=BoundDatum("datum", "scalar", "extra", "offset", Transform()),
        suppressed=RecordKind == "Global",
        configuration_states=(
            (FeatureCfgState("default", suppressed=True),)
            if RecordKind == "ConfigState"
            else ()
        ),
    )
    return ReplaceData(
        Document,
        configurations=(
            ReplaceData(
                Document.configurations[0],
                suppressed_feature_ids=(
                    (StepValue.id,) if RecordKind == "ConfigRecord" else ()
                ),
            ),
        ),
        parameters=tuple(
            Parameter(
                Identity,
                Identity,
                ParameterValue(0.0, ValueKind.KLength, "mm"),
                owner_id=StepValue.id,
            )
            for Identity in ("scalar", "extra")
        ),
        support_planes=(SupportPlane("datum", "Plane", Transform()),),
        feature_timeline=(StepValue,),
        metadata={},
    )
