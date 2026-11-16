from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureCfgState


# suppression coverage needs valid dependency graphs across global and configuration state
def BuildInactive(RecordKind: str) -> CadDocument:
    Document = MakeFusionDoc(
        DocumentSpec(
            "Active history",
            "height",
            20.0,
            ProfileKind="circle" if RecordKind == "InactiveReference" else "cuboid",
            ConstrainRectangle=RecordKind != "InactiveReference",
        )
    )
    Features = list(Document.feature_timeline)
    if RecordKind == "InactiveReference":
        Features.append(
            ReplaceData(Features[0], id="inactive", order=1, suppressed=True)
        )
    elif RecordKind == "Unordered":
        Features.reverse()
    else:
        StepIndex = (
            0
            if RecordKind
            in (
                "Dependency",
                "Transitive",
                "ConfigDependency",
                "ConfigRecordDependency",
            )
            else -1
        )
        Features[StepIndex] = ReplaceData(
            Features[StepIndex],
            suppressed=RecordKind in ("Final", "Dependency", "Transitive"),
            configuration_states=(
                (FeatureCfgState(Document.configurations[0].id, suppressed=True),)
                if RecordKind in ("ConfigState", "ConfigDependency")
                else ()
            ),
        )
        if RecordKind == "Transitive":
            Features.insert(
                1,
                ReplaceData(
                    Features[0],
                    id="bridge",
                    order=1,
                    input_feature_ids=(Features[0].id,),
                    suppressed=False,
                ),
            )
            Features[-1] = ReplaceData(
                Features[-1], order=2, input_feature_ids=("bridge",)
            )
        if RecordKind in ("ConfigRecord", "ConfigRecordDependency"):
            Document = ReplaceData(
                Document,
                configurations=(
                    ReplaceData(
                        Document.configurations[0],
                        suppressed_feature_ids=(Features[StepIndex].id,),
                    ),
                ),
            )
    return ReplaceData(
        Document,
        feature_timeline=tuple(Features),
        metadata=Document.metadata if RecordKind == "Unordered" else {},
    )
