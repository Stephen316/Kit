from dataclasses import asdict as DataMapping
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson

from pytest import mark as MarkTests

from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.convert.formats.FusionCodec.TSpline.ReadTsmCases import ReadTsmCases
from tests.convert.formats.FusionCodec.TSpline.ReadTsmFile import ReadTsmFile
from tests.convert.formats.FusionCodec.TSpline.TsmCase import TsmCase


@MarkTests.parametrize(
    "CaseValue", ReadTsmCases(), ids=lambda CaseValue: CaseValue["Name"]
)
def TestTsmArchive(CaseValue: TsmCase) -> None:
    Payload = ReadTsmFile(CaseValue)
    Model = ReadTspline(Payload)
    Encoded = DumpJson(
        DataMapping(Model), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    assert HashBytes(Encoded).hexdigest() == CaseValue["SemanticHash"]
    assert len(Model.Topology.Faces) == CaseValue["Faces"]
    assert len(Model.Topology.Vertices) == CaseValue["Vertices"]
    assert len(Model.Grips) == CaseValue["Grips"]
    assert EmitTspline(Model) == Payload
    assert ReadTspline(EmitTspline(Model)) == Model
