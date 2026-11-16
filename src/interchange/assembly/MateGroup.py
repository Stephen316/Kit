from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.assembly.MateGroupView import MateGroupView
from interchange.Core.Common import FreezeMapping
from interchange.Core.ModelBase import ModelBase, ModelDataMut
from interchange.Core.ModelExtras import ModelExtras
from interchange.Records.RecordProvenance import Provenance


# mate groups retain source ordering and hierarchy for editable organization
@ModelDataMut
class MateGroup(MateGroupView, ModelExtras, ModelBase):
    id: str
    name: str
    owner_definition_id: str
    mate_ids: tuple[str, ...]
    parent_group_id: str = ""
    order: int = 0
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
