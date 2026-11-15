from pathlib import Path as FilePath

from pytest import mark as MarkTests
from pytest import raises as RaisesError

from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.convert.formats.FusionCodec.TSpline.MutateTsm import MutateTsm
from tests.convert.formats.FusionCodec.TSpline.ReadTsmCases import ReadTsmCases
from tests.convert.formats.FusionCodec.TSpline.ReadTsmFile import ReadTsmFile


@MarkTests.parametrize(
    "Fault", ("mate", "flags", "owner", "number", "arity", "unknown", "cap", "star")
)
def TestTsmReject(Fault: str, TmpPath: FilePath) -> None:
    CaseValue = next(
        Value for Value in ReadTsmCases() if Value["Name"] == "PlaneCreased"
    )
    InputPath = TmpPath / "Malformed.tsm"
    _ = InputPath.write_bytes(MutateTsm(ReadTsmFile(CaseValue), Fault))
    with RaisesError(ValueError):
        _ = ReadTspline(InputPath.read_bytes())
