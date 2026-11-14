from functools import cache as CacheValue
from json import loads as LoadJson
from lzma import decompress as Decompress
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.convert.formats.FusionCodec.TSpline.TsmCase import TsmCase


@CacheValue
def ReadTsmCases() -> tuple[TsmCase, ...]:
    DataPath = FilePath(__file__).with_name("TsmSources.xz")
    return tuple(CastValue(list[TsmCase], LoadJson(Decompress(DataPath.read_bytes()))))
