import json as JsonCodec
from pathlib import Path as FilePath

from pytest import approx as ApproxValue, mark as TestMark

from tests.Convert.Solidworks.Core.InchIndex.DecodeInchCase import DecodeInchCase
from tests.Convert.Solidworks.Core.InchIndex.InchRoster import InchRoster


# small and large rosters check consistent ownership without depending on decoding order
@TestMark.parametrize("Count", (1, 256))
def TestOwnedInches(TmpPath: FilePath, Count: int) -> None:
    Model = JsonCodec.loads(DecodeInchCase(TmpPath, *InchRoster(Count)))
    assert len(Model["scalars"]) == Count
    assert len(Model["features"]) == 5
    assert Model["diagnostics"] == []
    ScalarsByName = {Scalar["name"]: Scalar for Scalar in Model["scalars"]}
    for Feature in Model["features"]:
        assert len(Feature["dimensions"]) == Count
        for Dimension in Feature["dimensions"]:
            Scalar = ScalarsByName[Dimension["name"]]
            assert Dimension["native_offset"] == Scalar["value_offset"]
            assert Dimension["native_value"] == Scalar["value"]
            assert Dimension["value_mm"] == ApproxValue(Scalar["value"] * 1000)
            assert Dimension["native_role"] == "driving"
            assert Dimension["operands"] == Scalar["operands"]
            assert Dimension["inch_display_value"] is None
