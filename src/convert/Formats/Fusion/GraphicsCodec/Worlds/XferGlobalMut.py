from __future__ import annotations
from typing import TYPE_CHECKING
from convert.Formats.Fusion.GraphicsCodec.Schema.GlobalVersions import (
    KGlobalVersions,
    KOptionalVersions,
)

from convert.Formats.Fusion.GraphicsCodec.Model.State.SceneGlobals import SceneGlobals

if TYPE_CHECKING:
    from convert.Formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


# transfer global needs an explicit validity boundary so display geometry retains its entity and scene relationships
def XferGlobalMut(State: SceneCodec, Value: SceneGlobals | None) -> SceneGlobals:
    Count = State.CountValue(len(Value.Versions) if Value else None)
    Versions: list[tuple[str, int]] = []
    for Index in range(Count):
        ClassName = State.TextValue(Value.Versions[Index][0] if Value else None)
        Version = State.Integer(Value.Versions[Index][1] if Value else None)
        Versions.append((ClassName, Version))
    Environment = State.TextValue(Value.Environment if Value else None)
    Names = {ClassName for ClassName, _ in Versions}
    if (
        len(Names) != len(Versions)
        or not set(KGlobalVersions) - KOptionalVersions <= Names
        or any(
            Version not in KGlobalVersions.get(ClassName, ())
            for ClassName, Version in Versions
        )
        or Environment != "RiverRubicon"
    ):
        raise ValueError("Unsupported graphics serializer versions or environment")
    return SceneGlobals(tuple(Versions), Environment)
