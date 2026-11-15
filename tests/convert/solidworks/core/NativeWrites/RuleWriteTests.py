from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.solidworks.core.NativeWrites.RejectFields import RejectFields
from tests.convert.solidworks.core.NativeWrites.RuleEvidence import RuleEvidence


# writers must preserve refusal when sketch relation identities or semantics are incomplete
@TestMark.parametrize(
    "ModeValue",
    (
        "native",
        "unknown",
        "empty",
        "entity",
        "parameter",
        "absent",
        "saved_empty",
        "sketch_parameter",
    ),
)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("IsSuppressed", (False, True))
def TestRuleWrite(
    TmpPath: FilePath, ModeValue: str, IsNested: bool, IsSuppressed: bool
) -> None:
    RejectFields(RuleEvidence(ModeValue, IsSuppressed), TmpPath, IsNested)


# dimension rules must carry parameter bindings for the target to remain editable
@TestMark.parametrize(
    "DimensionKind",
    ("distance", "distance_x", "distance_y", "angle", "radius", "diameter"),
)
def TestDimWrite(TmpPath: FilePath, DimensionKind: str) -> None:
    RejectFields(RuleEvidence("absent", False, DimensionKind), TmpPath, False)
