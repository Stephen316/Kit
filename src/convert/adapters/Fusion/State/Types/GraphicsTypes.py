from convert.formats.Fusion.GraphicsCodec.Model.Nodes.BodyChild import BodyChild
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.GeoValue import GeoValue
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.GroupValue import GroupValue
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.LodValue import LodValue
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.NodePayload import NodePayload
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.NodeValue import NodeValue
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.PrimitiveLod import PrimitiveLod
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.RenderFrame import RenderFrame
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.SceneWorld import SceneWorld
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.SketchWorld import SketchWorld
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.TextValue import TextValue
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene
from convert.formats.Fusion.GraphicsCodec.Model.State.SceneGlobals import SceneGlobals
from convert.formats.Fusion.GraphicsCodec.Model.State.SceneObject import SceneObject
from convert.formats.Fusion.GraphicsCodec.Model.Values.AppliedSet import AppliedSet
from convert.formats.Fusion.GraphicsCodec.Model.Values.CacheData import CacheData
from convert.formats.Fusion.GraphicsCodec.Model.Values.CircleArcValue import (
    CircleArcValue,
)
from convert.formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef
from convert.formats.Fusion.GraphicsCodec.Model.Values.FatPoint import FatPoint
from convert.formats.Fusion.GraphicsCodec.Model.Values.FieldValue import FieldValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.GraphicAttr import GraphicAttr
from convert.formats.Fusion.GraphicsCodec.Model.Values.IndexData import IndexData
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.formats.Fusion.GraphicsCodec.Model.Values.QualifierValue import (
    QualifierValue,
)
from convert.formats.Fusion.GraphicsCodec.Model.Values.RenderMesh import RenderMesh
from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet
from convert.formats.Fusion.GraphicsCodec.Model.Values.SimpleMesh import SimpleMesh
from convert.formats.Fusion.GraphicsCodec.Model.Values.StyleValue import StyleValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.TextureCache import TextureCache
from convert.formats.Fusion.GraphicsCodec.Model.Values.TextureValue import TextureValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexData import VertexData
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexField import VertexField
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexFormat import VertexFormat

KGraphicsTypes: tuple[type[object], ...] = (
    BodyChild,
    BrepWorld,
    GeoValue,
    GroupValue,
    LodValue,
    NodePayload,
    NodeValue,
    PrimitiveLod,
    RenderFrame,
    SceneWorld,
    SketchWorld,
    TextValue,
    GraphicScene,
    SceneGlobals,
    SceneObject,
    AppliedSet,
    CacheData,
    CircleArcValue,
    EntityRef,
    FatPoint,
    FieldValue,
    GraphicAttr,
    IndexData,
    ObjectRef,
    QualifierValue,
    RenderMesh,
    SceneSet,
    SimpleMesh,
    StyleValue,
    TextureCache,
    TextureValue,
    VertexData,
    VertexField,
    VertexFormat,
)
