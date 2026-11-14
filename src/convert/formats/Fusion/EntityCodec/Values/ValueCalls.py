from collections.abc import Callable
from typing import TypeAlias

from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.MetaCursor import MetaCursor

KReadValue: TypeAlias = Callable[
    [MetaCursor, WireType, EntityCatalog, int], KEntityValue
]
KEmitValue: TypeAlias = Callable[[KEntityValue, WireType, EntityCatalog, int], bytes]
