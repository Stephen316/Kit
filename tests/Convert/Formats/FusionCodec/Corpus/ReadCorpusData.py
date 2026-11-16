from functools import cache as CacheValue
from json import loads as LoadJson
from lzma import decompress as Decompress
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Formats.FusionCodec.Corpus.CorpusTypes import CorpusSchema

# schema path needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KSchemaPath = FilePath(__file__).with_name("CorpusSources.xz")


# shared read corpus data setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
@CacheValue
def ReadCorpusData() -> CorpusSchema:
    return CastValue(CorpusSchema, LoadJson(Decompress(KSchemaPath.read_bytes())))
