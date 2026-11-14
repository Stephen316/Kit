from json import loads as LoadJson
from pathlib import Path
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import ReadObject

KDefaultFiles = ("FeatureDefaults.json", "PasteDefaults.json")


def FeatureDefaults() -> dict[str, dict[str, object]]:
    Result: dict[str, dict[str, object]] = {}
    for FileName in KDefaultFiles:
        Source = Path(__file__).parent / FileName
        Content = Source.read_text(encoding="utf-8")
        Values = ReadObject(CastValue(object, LoadJson(Content)))
        for NameValue, Fields in Values.items():
            Result[NameValue] = dict(ReadObject(Fields))
    return Result
