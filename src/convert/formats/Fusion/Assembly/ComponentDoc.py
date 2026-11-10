# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Mapping
from dataclasses import replace as Replace

from convert.formats.Fusion.Assembly.ComponentScope import KScopeRecord
from convert.formats.Fusion.Topology.BodyEvidence import KBodyInventoryKey
from interchange.brep.topology.BrepModel import BrepModel
from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentCaps import InferCaps
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordParameter import Parameter
from interchange.records.RecordSource import CadSource


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
