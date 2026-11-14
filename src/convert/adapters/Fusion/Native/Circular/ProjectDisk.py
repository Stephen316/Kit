from convert.adapters.Fusion.Native.Circular.ProjectCircle import (
    CircleSketch,
    CircleFeature,
)
from convert.adapters.Fusion.Native.Circular.CheckSketchOnly import CheckSketchOnly
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckCircular import (
    CheckCircular,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.SelectSketch import SelectSketch
from convert.adapters.Fusion.Native.Parameters.ReadUsers import ReadUsers
from convert.adapters.Fusion.Native.Policy.CheckGraph import CheckBase
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckSceneRefs
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordSource import CadSource


def ProjectDisk(
    Model: DocumentModel, Source: CadSource, Graph: NativeGraph
) -> CadDocument:
    Context = SelectSketch(Graph)
    CheckBase(Graph, Context)
    CheckScopes(Graph, Context, Model.Asset.AssetId)
    Shape = ReadCircle(Graph, Context)
    Parameters = ReadUsers(Graph, Context)
    CheckSketchOnly(Graph, Context, Model)
    CheckCircular(Model, Shape, None, None)
    CheckSceneRefs(Graph, Model.Graphics)
    Title = dict(Model.Asset.Properties).get("documentName", "")
    Document = CadDocument(
        Source,
        (Configuration("default", Title, True),),
        Parameters,
        (SupportPlane(Context.Plane.Identity, "XY", Transform()),),
        (CircleSketch(Context, Shape),),
        (),
        (CircleFeature(Context),),
        (),
        metadata={"fusion.native_state": {"version": 2, "model": EncodeState(Model)}},
    )
    Document.AssertValid()
    return Document
