from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as RaisesError

from tests.convert.formats.FusionCodec.Brep.GeometryState.BreakIncidence import (
    BreakIncidence,
)
from tests.convert.formats.FusionCodec.Brep.GeometryState.GeometryArchive import (
    GeometryArchive,
)
from tests.convert.formats.FusionCodec.Brep.GeometryState.NativeGeometry import (
    NativeGeometry,
)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Fault", ("partner", "loop", "reflexive"))
def TestIncidence(TmpPath: FilePath, Fault: str) -> None:
    Original = NativeGeometry()
    Altered = BreakIncidence(Original, Fault)
    assert Altered != Original
    with RaisesError(ValueError):
        _ = GeometryArchive(TmpPath / "BrokenIncidence.zip", Altered)
