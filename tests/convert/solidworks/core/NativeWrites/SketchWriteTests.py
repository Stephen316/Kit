from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.solidworks.core.NativeWrites.RejectFields import RejectFields
from tests.convert.solidworks.core.NativeWrites.SketchEvidence import SketchEvidence


@TestMark.parametrize("ModeValue", ("payload", "kind", "unknown"))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("IsSuppressed", (False, True))
def TestSketchWrite(
    TmpPath: FilePath, ModeValue: str, IsNested: bool, IsSuppressed: bool
) -> None:
    RejectFields(SketchEvidence(ModeValue, IsSuppressed), TmpPath, IsNested)
