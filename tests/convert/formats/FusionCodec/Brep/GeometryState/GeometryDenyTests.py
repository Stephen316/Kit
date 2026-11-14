from pathlib import Path as FilePath
from struct import pack as PackValue
from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as RaisesError

from tests.convert.formats.FusionCodec.Brep.GeometryState.GeometryArchive import (
    GeometryArchive,
)
from tests.convert.formats.FusionCodec.Brep.GeometryState.NativeGeometry import (
    NativeGeometry,
)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Fault", ("roots", "trailing", "attribute"))
def TestGeometryBad(TmpPath: FilePath, Fault: str) -> None:
    Payload = NativeGeometry()
    if Fault == "roots":
        Payload = Payload[:31] + PackValue("<q", 3) + Payload[39:]
    elif Fault == "trailing":
        Payload += b"unknown"
    else:
        Payload = Payload.replace(
            b"generic_tag_attrib_def", b"unknown_tag_attrib_def", 1
        )
    with RaisesError(ValueError):
        _ = GeometryArchive(TmpPath / "InvalidGeometry.zip", Payload)
