from convert.adapters.Fusion.Native.Circular.CheckRoundBody import CheckRoundBody
from convert.adapters.Fusion.Native.Circular.CheckRoundTags import CheckRoundTags
from convert.adapters.Fusion.Native.Circular.ProjectCircle import (
    CircleSketch,
    CircularBody,
)
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.RotaryShape import RotaryShape
from convert.adapters.Fusion.Native.Circular.RotaryMass import RotaryMass
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckCircular import (
    CheckCircular,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Parameters.ReadParameters import ReadParameters
from convert.adapters.Fusion.Native.Policy.CheckGraph import CheckGraph
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckSceneRefs
from convert.adapters.Fusion.Native.Rectangle.CheckBodyJoins import CheckBodyJoins
from convert.adapters.Fusion.Native.Rectangle.CheckOperations import CheckOperations
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion
from convert.adapters.Fusion.Native.Projection.ProjectRectangle import ProjectFeatures
from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordSource import CadSource


def ProjectRound(
    Model: DocumentModel, Source: CadSource, Graph: NativeGraph
) -> CadDocument:
    Context = SelectExtrusion(Graph)
    CheckGraph(Graph, Context)
    CheckScopes(Graph, Context, Model.Asset.AssetId)
    Shape = ReadCircle(Graph, Context)
    Parameters = ReadParameters(Graph, Context, True)
    CheckRegion(Graph, Context, (Shape.CurveNode,), Model.Asset.AssetId)
    History = CheckBodyJoins(Graph, Context, Model)
    if not isinstance(History, (HistoryModel, FrustumHistory)):
        raise ValueError("Native circular extrusion requires analytic circular history")
    CheckOperations(Graph, Context, History, 2)
    CheckRoundTags(Graph, Context, Shape, History.Identity.OperationId, History.TagSet)
    CheckRoundBody(Graph, Context, History.TagSet)
    Solid = RotaryShape(Context, Shape, History)
    RotaryMass(Context, Solid)
    CheckCircular(Model, Shape, History, Solid)
    CheckSceneRefs(Graph, Model.Graphics)
    Material = ReadMaterial(Graph, Context, Model)
    Geometry, BodyValue = CircularBody(Context, Shape, Solid, Material.id)
    Title = dict(Model.Asset.Properties).get("documentName", "")
    Document = CadDocument(
        Source,
        (Configuration("default", Title, True),),
        Parameters,
        (SupportPlane(Context.Plane.Identity, "XY", Transform()),),
        (CircleSketch(Context, Shape),),
        (),
        ProjectFeatures(Graph, Context),
        (BodyValue,),
        brep=Geometry,
        materials=(Material,),
        metadata={"fusion.native_state": {"version": 2, "model": EncodeState(Model)}},
    )
    Document.AssertValid()
    return Document
