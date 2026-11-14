from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Nodes.XferFrameMut import XferFrameMut
from convert.formats.Fusion.GraphicsCodec.Geometry.XferGeometryMut import (
    XferGeometryMut,
)

from convert.formats.Fusion.GraphicsCodec.Model.Nodes.GeoValue import GeoValue

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferGeoNodeMut(State: SceneCodec, Value: GeoValue | None) -> GeoValue:
    Frame = XferFrameMut(State, Value.Frame if Value else None)
    Geometry = XferGeometryMut(State, Value.Geometry if Value else None)
    Bounds = State.Vector(Value.Bounds if Value else None, 6, "<d")
    State.EmptyLinks(1)
    return GeoValue(Frame, Geometry, Bounds)
