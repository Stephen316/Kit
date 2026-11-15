from collections.abc import Callable
from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType

# the value converter shape must stay shared so document reconstruction uses one contract for compatible values
KValueConverter: TypeAlias = Callable[
    [object, WireType, dict[str, NativeSchema]], KEntityValue
]
