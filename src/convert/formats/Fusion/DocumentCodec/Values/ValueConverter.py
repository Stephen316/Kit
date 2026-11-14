from collections.abc import Callable
from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType

KValueConverter: TypeAlias = Callable[
    [object, WireType, dict[str, NativeSchema]], KEntityValue
]
