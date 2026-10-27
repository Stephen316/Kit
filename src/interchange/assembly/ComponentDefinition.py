# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.assembly.DefinitionView import DefinitionView
from interchange.assembly.DefinitionRefs import DefinitionRefs
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.core.ModelExtras import ModelExtras
from interchange.records.RecordProvenance import Provenance


# component definitions describe reusable nodes independently from their occurrences
@ModelDataMut
class ComponentDef(DefinitionView, DefinitionRefs, ModelExtras, ModelBase):
    id: str
    name: str
    kind: ComponentKind | str
    document_id: str = ""
    configuration_name: str = ""
    configuration_id: str = ""
    bounding_box: BoundingBox | None = None
    body_ids: tuple[str, ...] = ()
    mesh_ids: tuple[str, ...] = ()
    source_path: str = ""
    source_format_id: str = ""
    source_sha256: str = ""
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
