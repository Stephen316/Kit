from functools import cache as CacheValue
from json import loads as LoadJson
from lzma import decompress as Decompress
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.convert.formats.FusionCodec.Mesh.MeshCase import MeshCase


@CacheValue
def ReadMeshCases() -> tuple[MeshCase, ...]:
    DataPath = FilePath(__file__).with_name("MeshSources.xz")
    return tuple(CastValue(list[MeshCase], LoadJson(Decompress(DataPath.read_bytes()))))
