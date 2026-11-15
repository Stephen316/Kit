from collections.abc import Callable
from typing import TypeAlias

from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.MetaCursor import MetaCursor

# the read value shape must stay shared so entity reconstruction uses one contract for compatible values
KReadValue: TypeAlias = Callable[
    [MetaCursor, WireType, EntityCatalog, int], KEntityValue
]

# the emit value shape must stay shared so entity reconstruction uses one contract for compatible values
KEmitValue: TypeAlias = Callable[[KEntityValue, WireType, EntityCatalog, int], bytes]
