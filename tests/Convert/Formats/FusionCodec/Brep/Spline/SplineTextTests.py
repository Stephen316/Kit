from pytest import mark as MarkTests, raises as RaisesError

from convert.Formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Reading.CountPoles import (
    CountPoles,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadPatches import (
    ReadPatches,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Writing.WideWord import WideWord
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Writing.WritePatches import (
    WritePatches,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.EmitWireField import (
    EmitWireField,
)


# the patch text contract needs boundary coverage so stored document relationships remain consistent
def TestPatchText() -> None:
    Regions = (
        (
            PatchCell(0, (0, 1, 0, 1), (0, 0, 0)),
            PatchCell(1, (0, 1, 0, 1), (0, -1, 0)),
        ),
        (PatchCell(2, (0, 1, 0, 1), (-2, -1, 0)),),
    )
    PatchText = WritePatches(Regions)
    assert PatchText == (
        "0 2\n2 0 0 1 0 1 0 0 0 1 0 1 0 1 0 -1 0 \n1 2 0 1 0 1 -2 -1 0 \n"
    )
    assert ReadPatches(PatchText) == Regions


# the patch words contract needs boundary coverage so stored document relationships remain consistent
def TestPatchWords() -> None:
    Regions = (
        (
            PatchCell(0, (0, 0.5, 0, 0.5), (0, -0.5, 0)),
            PatchCell(1, (0, 1 / 3, 0, 1), (-1.5, 0, 1)),
        ),
    )
    PatchText = WritePatches(Regions)
    assert PatchText == (
        "0 1\n2 0 0 0.5 0 0.5 0 -0.5 0 1 0 0.33333333333333331 0 1 -1.5 0 1 \n"
    )
    assert ReadPatches(PatchText) == Regions


# the patch deny contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize(
    "TextValue",
    (
        "0 1\n1 0 0 1.0 0 1 0 0 0 \n",
        "0 1\n1 0.5 0 1 0 1 0 0 0 \n",
        "0 1\n1 0 0 1 0 1 0 0 0.5 \n",
        "0 1\n1 0 0 nan 0 1 0 0 0 \n",
        "0 1\n1 0 0 1 0 1 0 0 0\n",
        "0 2\n1 0 0 1 0 1 0 0 0 \n",
        "1 1\n1 0 0 1 0 1 0 0 0 \n",
        "0 1\n1 +0 0 1 0 1 0 0 0 \n",
        "0 1\n2 0 0 1 0 1 0 0 0 \n",
    ),
)
def TestPatchDeny(TextValue: str) -> None:
    with RaisesError(ValueError):
        _ = ReadPatches(TextValue)


# the wide text contract needs boundary coverage so stored document relationships remain consistent
def TestWideText() -> None:
    assert WideWord("a" * 255) == (7, "a" * 255)
    assert WideWord("a" * 256) == (8, "a" * 256)
    assert EmitWireField((8, "a" * 256)) == b"\x08\x00\x01" + b"a" * 256
    assert EmitWireField((13, "nubs")) == b"\x0d\x04nubs"
    assert EmitWireField((21, 3)) == b"\x15\x03" + bytes(7)
    assert WideWord("a" * 32767) == (8, "a" * 32767)
    assert WideWord("a" * 32768) == (9, "a" * 32768)
    assert EmitWireField((9, "a" * 32768)) == b"\x09\x00\x80" + bytes(6) + b"a" * 32768
    with RaisesError(ValueError):
        _ = EmitWireField((8, "a" * 32768))


# the pole count contract needs boundary coverage so stored document relationships remain consistent
def TestPoleCount() -> None:
    Knots = (SplineKnot(0.0, 3), SplineKnot(1.0, 1), SplineKnot(2.0, 3))
    assert CountPoles(Knots, 3) == 5
    with RaisesError(ValueError):
        _ = CountPoles((SplineKnot(0.0, 4), SplineKnot(1.0, 4)), 3)
    with RaisesError(ValueError):
        _ = CountPoles((SplineKnot(1.0, 3), SplineKnot(0.0, 3)), 3)
