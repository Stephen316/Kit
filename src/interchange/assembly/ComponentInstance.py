from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.assembly.InstanceFlags import InstanceFlags
from interchange.assembly.InstanceView import InstanceView
from interchange.Core.Common import FreezeMapping
from interchange.Core.ModelBase import ModelBase, ModelDataMut
from interchange.Core.ModelExtras import ModelExtras
from interchange.Records.RecordProvenance import Provenance
from interchange.assembly.TransformMatrix import TransformMatrix, KIdentityMatrix


# component instances preserve placement order suppression and configuration choices
@ModelDataMut
class ComponentInst(InstanceView, InstanceFlags, ModelExtras, ModelBase):
    id: str
    name: str
    definition_id: str
    owner_definition_id: str
    transform: TransformMatrix = KIdentityMatrix
    order: int = 0
    reference_number: str = ""
    configuration_name: str = ""
    configuration_id: str = ""
    suppressed: bool = False
    hidden: bool = False
    fixed: bool = False
    flexible: bool = False
    exclude_from_bom: bool = False
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
