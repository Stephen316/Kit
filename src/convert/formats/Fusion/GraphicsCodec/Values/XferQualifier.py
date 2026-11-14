from __future__ import annotations
from typing import TYPE_CHECKING

from convert.formats.Fusion.GraphicsCodec.Model.Values.QualifierValue import (
    QualifierValue,
)

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferQualifier(State: SceneCodec, Value: QualifierValue | None) -> QualifierValue:
    return QualifierValue(State.OptionalText(Value.ImagePath if Value else None))
