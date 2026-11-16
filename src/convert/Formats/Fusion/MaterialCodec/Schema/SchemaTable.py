from typing import TypeAlias

from convert.Formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec

# the schema table shape must stay shared so material reconstruction uses one contract for compatible values
KSchemaTable: TypeAlias = dict[str, tuple[PropertySpec, ...]]
