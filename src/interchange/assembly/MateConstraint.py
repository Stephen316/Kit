from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.assembly.AssemblyEnums import MateAlignment, MateKind
from interchange.assembly.ConstraintDrive import ConstraintDrive
from interchange.assembly.ConstraintView import ConstraintView
from interchange.Core.Common import FreezeMapping
from interchange.Core.ModelBase import ModelBase, ModelDataMut
from interchange.Core.ModelExtras import ModelExtras
from interchange.Records.RecordParameter import ParameterValue
from interchange.Records.RecordProvenance import Provenance


# mate constraints preserve relationships values and bindings across systems
@ModelDataMut
class MateConstraint(ConstraintView, ConstraintDrive, ModelExtras, ModelBase):
    id: str
    name: str
    kind: MateKind | str
    owner_definition_id: str
    entity_ids: tuple[str, ...]
    order: int = 0
    value: ParameterValue | None = None
    parameter_ids: tuple[str, ...] = ()
    alignment: MateAlignment | str = MateAlignment.KUnknown
    suppressed: bool = False
    driving: bool = True
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
