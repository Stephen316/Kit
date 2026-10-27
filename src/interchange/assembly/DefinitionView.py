# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import cast as CastValue

from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.geometry.models.BoundingBox import BoundingBox


# definition consumers read identity and variant state through one typed view
class DefinitionView:
    __slots__ = ()

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return CastValue(str, getattr(self, "id"))

    # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return CastValue(str, getattr(self, "name"))

    # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> ComponentKind | str:
        return CastValue(ComponentKind | str, getattr(self, "kind"))

    # owning document id keeps definitions linkable across container boundaries
    @property
    def DocumentId(self) -> str:
        return CastValue(str, getattr(self, "document_id"))

    # configuration label keeps variant identity visible without resolving parameters
    @property
    def ConfigurationName(self) -> str:
        return CastValue(str, getattr(self, "configuration_name"))

    # configuration id keeps variant references stable across renames
    @property
    def ConfigurationId(self) -> str:
        return CastValue(str, getattr(self, "configuration_id"))

    # cached bounds keep spatial filtering cheap for large assemblies
    @property
    def BoundingBox(self) -> BoundingBox | None:
        return CastValue(BoundingBox | None, getattr(self, "bounding_box"))
