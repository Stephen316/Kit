from collections.abc import Callable
from typing import TypeAlias

from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.MetaCursor import MetaCursor

# the read value shape must stay shared so entity reconstruction uses one contract for compatible values
KReadValue: TypeAlias = Callable[
    [MetaCursor, WireType, EntityCatalog, int], KEntityValue
]

# the emit value shape must stay shared so entity reconstruction uses one contract for compatible values
KEmitValue: TypeAlias = Callable[[KEntityValue, WireType, EntityCatalog, int], bytes]
