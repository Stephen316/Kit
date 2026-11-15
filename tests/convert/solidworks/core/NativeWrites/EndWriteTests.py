from pathlib import Path as FilePath

from pytest import mark as TestMark

from interchange.features.FeatureExtrude import ExtrudeEnd
from tests.convert.solidworks.core.NativeWrites.EndEvidence import EndEvidence
from tests.convert.solidworks.core.NativeWrites.RejectFields import RejectFields


@TestMark.parametrize("Family", ("extrude", "second", "hole"))
@TestMark.parametrize(
    "EndValue", (ExtrudeEnd.NATIVE, "native:32767", "future:termination")
)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("IsSuppressed", (False, True))
def TestEndWrite(
    TmpPath: FilePath,
    Family: str,
    EndValue: ExtrudeEnd | str,
    IsNested: bool,
    IsSuppressed: bool,
) -> None:
    RejectFields(EndEvidence(Family, EndValue, IsSuppressed), TmpPath, IsNested)
