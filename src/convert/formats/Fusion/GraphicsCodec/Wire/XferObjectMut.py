from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Worlds.XferGroupMut import XferGroupMut
from convert.formats.Fusion.GraphicsCodec.Nodes.XferGeoNodeMut import XferGeoNodeMut
from convert.formats.Fusion.GraphicsCodec.Nodes.XferTextMut import XferTextMut
from convert.formats.Fusion.GraphicsCodec.Geometry.XferFormatMut import XferFormatMut
from convert.formats.Fusion.GraphicsCodec.Geometry.XferIndicesMut import XferIndicesMut
from convert.formats.Fusion.GraphicsCodec.Fields.XferStyleMut import XferStyleMut
from convert.formats.Fusion.GraphicsCodec.Schema.StyleRules import KStyleRules

from convert.formats.Fusion.GraphicsCodec.Model.State.KObjectValue import KObjectValue
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.GroupValue import GroupValue
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.GeoValue import GeoValue
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.TextValue import TextValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexFormat import VertexFormat
from convert.formats.Fusion.GraphicsCodec.Model.Values.IndexData import IndexData
from convert.formats.Fusion.GraphicsCodec.Model.Values.StyleValue import StyleValue

from convert.formats.Fusion.GraphicsCodec.Model.Values.RenderMesh import RenderMesh
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexData import VertexData
from convert.formats.Fusion.GraphicsCodec.Geometry.XferRenderMut import XferRenderMut
from convert.formats.Fusion.GraphicsCodec.Geometry.XferVerticesMut import XferVerticesMut

from convert.formats.Fusion.GraphicsCodec.Model.Values.CircleArcValue import CircleArcValue
from convert.formats.Fusion.GraphicsCodec.Geometry.XferCircleMut import XferCircleMut
from convert.formats.Fusion.GraphicsCodec.Model.Values.QualifierValue import (
    QualifierValue,
)
from convert.formats.Fusion.GraphicsCodec.Values.XferQualifier import XferQualifier
from convert.formats.Fusion.GraphicsCodec.Model.Values.NodePath import NodePath
from convert.formats.Fusion.GraphicsCodec.Values.XferPathMut import XferPathMut

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferObjectMut(
    State: SceneCodec, ClassName: str, Value: KObjectValue | None
) -> KObjectValue:
    if ClassName == "CircleArc<double>" and (Value is None or isinstance(Value, CircleArcValue)):
        return XferCircleMut(State, Value)
    if ClassName == "SimpleMesh" and (Value is None or isinstance(Value, RenderMesh)):
        return XferRenderMut(State, Value)
    if ClassName == "VertexBuffer" and (Value is None or isinstance(Value, VertexData)):
        return XferVerticesMut(State, Value)
    if ClassName == "GroupNode" and (Value is None or isinstance(Value, GroupValue)):
        return XferGroupMut(State, Value)
    if ClassName == "GeometryNode" and (Value is None or isinstance(Value, GeoValue)):
        return XferGeoNodeMut(State, Value)
    if ClassName == "FTextNode" and (Value is None or isinstance(Value, TextValue)):
        return XferTextMut(State, Value)
    if ClassName == "VertexFormat" and (
        Value is None or isinstance(Value, VertexFormat)
    ):
        return XferFormatMut(State, Value)
    if ClassName == "AIndexBuffer" and (Value is None or isinstance(Value, IndexData)):
        return XferIndicesMut(State, Value)
    if ClassName == "AlphaImageSelectionQualifier" and (
        Value is None or isinstance(Value, QualifierValue)
    ):
        return XferQualifier(State, Value)
    if ClassName == "PersistentPassiveNodePath" and (
        Value is None or isinstance(Value, NodePath)
    ):
        return XferPathMut(State, Value)
    if ClassName in KStyleRules and (Value is None or isinstance(Value, StyleValue)):
        return XferStyleMut(State, ClassName, Value)
    raise ValueError("Unsupported or inconsistent graphics object class")
