from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.GroupValue import GroupValue
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.GeoValue import GeoValue
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.TextValue import TextValue
from convert.Formats.Fusion.GraphicsCodec.Model.Values.VertexFormat import VertexFormat
from convert.Formats.Fusion.GraphicsCodec.Model.Values.IndexData import IndexData
from convert.Formats.Fusion.GraphicsCodec.Model.Values.StyleValue import StyleValue

from convert.Formats.Fusion.GraphicsCodec.Model.Values.RenderMesh import RenderMesh
from convert.Formats.Fusion.GraphicsCodec.Model.Values.VertexData import VertexData

from convert.Formats.Fusion.GraphicsCodec.Model.Values.CircleArcValue import (
    CircleArcValue,
)
from convert.Formats.Fusion.GraphicsCodec.Model.Values.QualifierValue import (
    QualifierValue,
)
from convert.Formats.Fusion.GraphicsCodec.Model.Values.NodePath import NodePath

# the object value variants need one shared contract so graphics reconstruction cannot omit a supported value shape
KObjectValue = (
    GroupValue
    | GeoValue
    | TextValue
    | VertexFormat
    | IndexData
    | StyleValue
    | RenderMesh
    | VertexData
    | CircleArcValue
    | QualifierValue
    | NodePath
)
