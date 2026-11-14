from math import isfinite

from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.WritePatches import (
    PatchWord,
)


def ReadPatchWord(WordText: str) -> float:
    try:
        Value: float = int(WordText)
    except ValueError:
        Value = float(WordText)
    if not isfinite(Value) or PatchWord(Value) != WordText:
        raise ValueError("Invalid Fusion T-spline patch word")
    return Value


def ReadWhole(Value: float) -> int:
    if not isinstance(Value, int):
        raise ValueError("Invalid Fusion T-spline patch index")
    return Value


def ReadPatchRow(LineText: str) -> tuple[PatchCell, ...]:
    Words = LineText.split(" ")
    if len(Words) < 2 or Words[-1]:
        raise ValueError("Invalid Fusion T-spline patch row")
    Numbers = tuple(ReadPatchWord(WordText) for WordText in Words[:-1])
    Count = ReadWhole(Numbers[0])
    if not 0 < Count <= 4096 or len(Numbers) != 1 + 8 * Count:
        raise ValueError("Invalid Fusion T-spline patch row size")
    return tuple(
        PatchCell(
            ReadWhole(Numbers[Start]),
            (
                Numbers[Start + 1],
                Numbers[Start + 2],
                Numbers[Start + 3],
                Numbers[Start + 4],
            ),
            (Numbers[Start + 5], Numbers[Start + 6], ReadWhole(Numbers[Start + 7])),
        )
        for Start in range(1, len(Numbers), 8)
    )
