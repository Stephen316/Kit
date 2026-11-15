from json import loads as LoadJson
from typing import cast as CastValue

from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartCases import (
    KOracleRoot,
)

# the reports cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KReports = (
    "Capture.json",
    "CaptureFamilies.json",
    "CaptureBodies.json",
    "CaptureSweeps.json",
    "CapturePastes.json",
)


# shared native bodies setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
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


# shared native control setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def NativeControl(NameValue: str) -> dict[str, object]:
    Bodies = NativeBodies(NameValue)
    assert len(Bodies) == 1
    return Bodies[0]
