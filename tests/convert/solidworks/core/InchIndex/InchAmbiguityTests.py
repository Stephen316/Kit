import json as JsonCodec
from pathlib import Path as FilePath

from tests.convert.solidworks.core.InchIndex.DecodeInchCase import DecodeInchCase
from tests.convert.solidworks.core.InchIndex.InchAmbiguity import InchAmbiguity


def TestInchProofs(TmpPath: FilePath) -> None:
    Model = JsonCodec.loads(DecodeInchCase(TmpPath, *InchAmbiguity()))
    Dimensions = {
        Dimension["name"]: Dimension for Dimension in Model["features"][0]["dimensions"]
    }
    assert len(Model["scalars"]) == 9
    assert Model["diagnostics"] == []
    for NameValue in (
        "Duplicate",
        "NoIdentity",
        "DisplayOnly",
        "WrongRound",
        "Precision",
    ):
        assert Dimensions[NameValue]["value_mm"] is None
        assert Dimensions[NameValue]["native_offset"] is None
        assert Dimensions[NameValue]["inch_display_value"] == 0.04
    for NameValue in ("Valid", "NativeRole", "ZeroIdentity"):
        assert Dimensions[NameValue]["value_mm"] == 1.0
        assert Dimensions[NameValue]["inch_display_value"] is None
    assert Dimensions["Valid"]["native_role"] == "driving"
    assert Dimensions["NativeRole"]["native_role"] == "native"
