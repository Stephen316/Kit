from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Convert.Solidworks.Core.NativeWrites.RejectFields import RejectFields
from tests.Convert.Solidworks.Core.NativeWrites.SketchEvidence import SketchEvidence


# native entities must remain guarded under nesting and feature suppression changes
@TestMark.parametrize("ModeValue", ("payload", "kind", "unknown"))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("IsSuppressed", (False, True))
def TestSketchWrite(
    TmpPath: FilePath, ModeValue: str, IsNested: bool, IsSuppressed: bool
) -> None:
    RejectFields(SketchEvidence(ModeValue, IsSuppressed), TmpPath, IsNested)
