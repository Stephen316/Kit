from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as Raises

from convert.formats.Fusion.DocumentCodec.Auxiliary.Configuration.EmitConfigPart import (
    EmitConfigPart,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Configuration.ReadConfigPart import (
    ReadConfigPart,
)
from tests.convert.formats.FusionCodec.Documents.Reading.AuxPartSource import (
    NativeAuxParts,
    StoreAuxPart,
)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("SourceIndex", (0, 1, 2))
def TestConfigParts(TmpPath: FilePath, SourceIndex: int) -> None:
    Parts = tuple(
        Value
        for Value in NativeAuxParts(SourceIndex)
        if not Value.Name.endswith(".smb")
    )
    assert len(Parts) == 2
    Decoded = tuple(ReadConfigPart(PartValue) for PartValue in Parts)
    assert {Value.KindValue for Value in Decoded} == {"table", "rule"}
    for Index, Value in enumerate(Decoded):
        Stored = StoreAuxPart(TmpPath / (str(Index) + ".zip"), EmitConfigPart(Value))
        assert ReadConfigPart(Stored) == Value
        assert Stored.Payload == b"{}"
        with Raises(ValueError, match="Nonempty Fusion configurations"):
            _ = ReadConfigPart(ReplaceValue(Stored, Payload=b'{"rows": []}'))
        with Raises(ValueError, match="role"):
            _ = EmitConfigPart(
                ReplaceValue(
                    Value, KindValue="rule" if Value.KindValue == "table" else "table"
                )
            )
