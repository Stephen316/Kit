from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.assembly.AssemblyEnums import MateEntityKind
from interchange.assembly.MateEntityView import MateEntityView
from interchange.Core.Common import FreezeMapping
from interchange.Core.ModelBase import ModelBase, ModelDataMut
from interchange.Core.ModelExtras import ModelExtras
from interchange.Records.RecordProvenance import Provenance
from interchange.assembly.TransformMatrix import TransformMatrix


# mate entities resolve constraint geometry through occurrence paths and optional frames
@ModelDataMut
class MateEntity(MateEntityView, ModelExtras, ModelBase):
    id: str
    owner_definition_id: str
    instance_path: tuple[str, ...]
    kind: MateEntityKind | str
    source_entity_id: str = ""
    selection_id: str = ""
    frame: TransformMatrix | None = None
    radius: float | None = None
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
