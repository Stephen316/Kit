from collections.abc import Mapping
from dataclasses import replace as Replace

from convert.Formats.Fusion.Assembly.ComponentScope import KScopeRecord
from convert.Formats.Fusion.Topology.BodyEvidence import KBodyInventoryKey
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentCaps import InferCaps
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter
from interchange.Records.RecordSource import CadSource


# reusable component documents retain local source semantics without copying the archive
def MakeAsmDoc(
    Document: CadDocument,
    Records: tuple[KScopeRecord, ...],
    Bodies: tuple[DesignBody, ...],
    Model: BrepModel,
    Evidence: Mapping[str, object],
) -> CadDocument:
    Steps = tuple(Value for Value in Records if isinstance(Value, FeatureStep))
    Parameters = tuple(Value for Value in Records if isinstance(Value, Parameter))
    StepIds = {Value.id for Value in Steps}
    ParameterIds = {Value.id for Value in Parameters}
    Result = CadDocument(
        source=CadSource(
            format_id=Document.source.format_id,
            path="",
            sha256="",
            container_version=Document.source.container_version,
            application_version=Document.source.application_version,
        ),
        configurations=tuple(
            Replace(
                CfgValue,
                overrides=tuple(
                    Value
                    for Value in CfgValue.overrides
                    if Value.parameter_id in ParameterIds
                ),
                suppressed_feature_ids=tuple(
                    Identity
                    for Identity in CfgValue.suppressed_feature_ids
                    if Identity in StepIds
                ),
            )
            for CfgValue in Document.configurations
        ),
        parameters=Parameters,
        support_planes=tuple(
            Value for Value in Records if isinstance(Value, SupportPlane)
        ),
        sketches=tuple(Value for Value in Records if isinstance(Value, Sketch)),
        selections=tuple(Value for Value in Records if isinstance(Value, Selection)),
        feature_timeline=Steps,
        bodies=Bodies,
        brep=Model,
        metadata=FreezeMapping({KBodyInventoryKey: Evidence}),
        units=Document.units,
        schema_version=Document.schema_version,
    )
    return Replace(
        Result,
        capabilities=(Document.capabilities & InferCaps(Result))
        | {Capability.KBrep, Capability.KBodyStructure},
    )
