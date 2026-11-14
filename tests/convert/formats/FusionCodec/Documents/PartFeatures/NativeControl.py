from json import loads as LoadJson
from typing import cast as CastValue

from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartCases import (
    KOracleRoot,
)

KReports = (
    "Capture.json",
    "CaptureFamilies.json",
    "CaptureBodies.json",
    "CaptureSweeps.json",
    "CapturePastes.json",
)


def NativeBodies(NameValue: str) -> list[dict[str, object]]:
    Found: list[dict[str, object]] = []
    for Source in KReports:
        Content = (KOracleRoot / "Controls" / Source).read_text()
        Report = CastValue(dict[str, object], LoadJson(Content))
        Controls = CastValue(list[dict[str, object]], Report["controls"])
        Found += [Control for Control in Controls if Control["name"] == NameValue]
    assert len(Found) == 1
    Observed = CastValue(dict[str, object], Found[0]["observed"])
    return CastValue(list[dict[str, object]], Observed["bodies"])


def NativeControl(NameValue: str) -> dict[str, object]:
    Bodies = NativeBodies(NameValue)
    assert len(Bodies) == 1
    return Bodies[0]
