from pathlib import Path as FilePath

from pytest import mark as MarkTests
from pytest import raises as RaisesError

from convert.Formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.Convert.Formats.FusionCodec.TSpline.MutateTsm import MutateTsm
from tests.Convert.Formats.FusionCodec.TSpline.ReadTsmCases import ReadTsmCases
from tests.Convert.Formats.FusionCodec.TSpline.ReadTsmFile import ReadTsmFile


# the tsm reject contract needs boundary coverage so stored document relationships remain consistent
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
