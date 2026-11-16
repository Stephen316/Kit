from collections.abc import Callable
from typing import TypeAlias

from convert.Formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType

# the value converter shape must stay shared so document reconstruction uses one contract for compatible values
KValueConverter: TypeAlias = Callable[
    [object, WireType, dict[str, NativeSchema]], KEntityValue
]
