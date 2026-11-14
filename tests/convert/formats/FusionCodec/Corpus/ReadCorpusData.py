from functools import cache as CacheValue
from json import loads as LoadJson
from lzma import decompress as Decompress
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.convert.formats.FusionCodec.Corpus.CorpusTypes import CorpusSchema

KSchemaPath = FilePath(__file__).with_name("CorpusSources.xz")


@CacheValue
def ReadCorpusData() -> CorpusSchema:
    return CastValue(CorpusSchema, LoadJson(Decompress(KSchemaPath.read_bytes())))
