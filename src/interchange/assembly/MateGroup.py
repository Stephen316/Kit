# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.assembly.MateGroupView import MateGroupView
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.core.ModelExtras import ModelExtras
from interchange.records.RecordProvenance import Provenance


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
