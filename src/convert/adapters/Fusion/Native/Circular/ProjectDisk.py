from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Native.Circular.ProjectCircle import (
    CircleSketch,
    CircleFeature,
)
from convert.adapters.Fusion.Native.Circular.CheckSketchOnly import CheckSketchOnly
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.ProjectRadial import ProjectRadial
from convert.adapters.Fusion.Native.Circular.RadialSpecs import KRadialSpecs
from convert.adapters.Fusion.Native.Circular.ReadRadialBinding import ReadSizeLinks
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
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource


# the project disk contract needs a shared interpretation so public geometry remains consistent with native circular topology
def ProjectDisk(
    Model: DocumentModel, Source: CadSource, Graph: NativeGraph
) -> CadDocument:
    Context = SelectSketch(Graph)
    Dimensions = tuple(
        NodeValue
        for NameValue in KRadialSpecs
        for NodeValue in Graph.ByClass(NameValue)
    )
    if len(Dimensions) > 1:
        raise ValueError("Native radial profile supports one sketch dimension")
    Dimension = Dimensions[0] if Dimensions else None
    CheckBase(Graph, Context, Dimension)
    CheckScopes(Graph, Context, Model.Asset.AssetId)
    Shape = ReadCircle(Graph, Context, Dimension)
    SketchValue = CircleSketch(Context, Shape)
    Feature = CircleFeature(Context)
    if Dimension is None:
        Parameters = ReadUsers(Graph, Context)
    else:
        Binding = ReadSizeLinks(Graph, Context, Dimension)
        Parameter, Relation = ProjectRadial(Binding, Context.SketchFeature)
        Parameters = (Parameter,)
        SketchValue = ReplaceData(
            SketchValue, constraints=(Relation,), parameter_ids=(Parameter.id,)
        )
        Feature = ReplaceData(Feature, parameter_ids=(Parameter.id,))
        if len(Model.Snapshots) != 1:
            raise ValueError("Native radial profile requires one saved sheet snapshot")
    CheckSketchOnly(Graph, Context, Model)
    CheckCircular(Model, Shape, None, None)
    CheckSceneRefs(Graph, Model.Graphics)
    Title = dict(Model.Asset.Properties).get("documentName", "")
    Metadata = (
        {"fusion.native_state": {"version": 2, "model": EncodeState(Model)}}
        if Dimension is None
        else {}
    )
    Document = CadDocument(
        Source,
        (Configuration("default", Title, True),),
        Parameters,
        (SupportPlane(Context.Plane.Identity, "XY", Transform()),),
        (SketchValue,),
        (),
        (Feature,),
        (),
        metadata=Metadata,
    )
    Document.AssertValid()
    return Document
