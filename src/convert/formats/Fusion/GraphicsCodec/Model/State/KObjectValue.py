from convert.formats.Fusion.GraphicsCodec.Model.Nodes.GroupValue import GroupValue
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.GeoValue import GeoValue
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.TextValue import TextValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexFormat import VertexFormat
from convert.formats.Fusion.GraphicsCodec.Model.Values.IndexData import IndexData
from convert.formats.Fusion.GraphicsCodec.Model.Values.StyleValue import StyleValue

from convert.formats.Fusion.GraphicsCodec.Model.Values.RenderMesh import RenderMesh
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexData import VertexData

from convert.formats.Fusion.GraphicsCodec.Model.Values.CircleArcValue import (
    CircleArcValue,
)
from convert.formats.Fusion.GraphicsCodec.Model.Values.QualifierValue import (
    QualifierValue,
)
from convert.formats.Fusion.GraphicsCodec.Model.Values.NodePath import NodePath

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
