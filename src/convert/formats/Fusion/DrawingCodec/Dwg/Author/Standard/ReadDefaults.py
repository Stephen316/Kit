from functools import cache as CacheValue
from json import loads as LoadJson
from pathlib import Path

from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import ReadObject
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import DraftRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.ReadDraftJson import (
    ReadDraftRecord,
)

KClassDefaults = dict[str, tuple[DraftRecord, DraftRecord]]


def ReadDefaults(Source: Path) -> KClassDefaults:
    Classes = ReadObject(LoadJson(Source.read_text(encoding="utf-8")))
    Result: KClassDefaults = {}
    for ClassName, Value in Classes.items():
        Parts = ReadObject(Value)
        Result[ClassName] = (
            ReadDraftRecord(Parts["Common"]),
            ReadDraftRecord(Parts["Data"]),
        )
    return Result


@CacheValue
def SheetDefaults() -> KClassDefaults:
    return ReadDefaults(Path(__file__).with_name("SheetDefaults.json"))
