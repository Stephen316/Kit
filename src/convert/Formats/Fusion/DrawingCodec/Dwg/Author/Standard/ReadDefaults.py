from functools import cache as CacheValue
from json import loads as LoadJson
from pathlib import Path

from convert.Formats.Fusion.DocumentCodec.Values.ReadObjects import ReadObject
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import DraftRecord
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Standard.ReadDraftJson import (
    ReadDraftRecord,
)

# the class defaults shape must stay shared so drawing standard authoring uses one contract for compatible values
KClassDefaults = dict[str, tuple[DraftRecord, DraftRecord]]


# the defaults operation needs a distinct decoding boundary so native drawing objects use a consistent symbol vocabulary
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


# the sheet defaults contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
@CacheValue
def SheetDefaults() -> KClassDefaults:
    return ReadDefaults(Path(__file__).with_name("SheetDefaults.json"))
