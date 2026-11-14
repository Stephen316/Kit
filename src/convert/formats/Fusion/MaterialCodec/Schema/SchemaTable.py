from typing import TypeAlias

from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec

KSchemaTable: TypeAlias = dict[str, tuple[PropertySpec, ...]]
