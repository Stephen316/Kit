from convert.adapters.Fusion.Native.DatumPrism.ReadDatumBody import ReadDatumBody
from convert.adapters.Fusion.Native.DatumPrism.ReadDatumFrame import (
    KYzMatrix,
    ReadDatumFrame,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Parameters.ReadParameters import ReadParameters
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import (
    CheckAuxiliary,
    CheckSceneRefs,
)
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Policy.CheckMassCache import CheckMassCache
from convert.adapters.Fusion.Native.Policy.CheckGraph import (
    CheckGraph,
    CheckShape,
)
from convert.adapters.Fusion.Native.Projection.ProjectRectangle import (
    ProjectBody,
    ProjectFeatures,
    ProjectSketch,
)
from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
from convert.adapters.Fusion.Native.Rectangle.CheckBodyJoins import CheckBodyJoins
from convert.adapters.Fusion.Native.Rectangle.CheckOperations import CheckOperations
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion
from convert.adapters.Fusion.Native.Rectangle.CheckPrismTags import CheckPrismTags
from convert.adapters.Fusion.Native.Rectangle.ReadRectangle import ReadRectangle
from convert.adapters.Fusion.Native.Rectangle.ReadRectRules import ReadRectRules
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.adapters.Fusion.Native.SignedPrism.CheckSignedTags import CheckSignedTags
from convert.adapters.Fusion.Native.SignedPrism.ReadSignedBody import ReadSignedBody
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Features.DistanceValues import GetDistValues
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import KTransformIdentity, Transform
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from interchange.Records.RecordParameter import Parameter


# project prism needs an explicit validity boundary so public document claims remain grounded in native records
def ProjectPrism(
    Model: DocumentModel, Source: CadSource, Graph: NativeGraph
) -> CadDocument:
    Context = SelectExtrusion(Graph)
    Station = GenericStation(Model, Context)
    Reverse = Station < 0.0
    YzDatum = Station > 0.0 and Context.Plane.Fields["transform"] == KYzMatrix
    Rectangle = ReadRectRules(Graph, Context, Reverse, YzDatum)
    CheckGraph(Graph, Context, Rectangle, YzDatum)
    CheckScopes(Graph, Context, Model.Asset.AssetId)
    FrameValue = ReadDatumFrame(Graph, Context) if YzDatum else KTransformIdentity
    Shape = ReadRectangle(Graph, Context, Rectangle)
    Parameters = ReadParameters(Graph, Context, Rectangle=Rectangle, Reverse=Reverse)
    CheckRegion(Graph, Context, Shape.LineNodes, Model.Asset.AssetId)
    CheckPrismBody(Graph, Context, Model, Shape, FrameValue, Reverse, YzDatum)
    Material = ReadMaterial(Graph, Context, Model)
    Features = ProjectFeatures(Graph, Context, Rectangle, FrameValue.z_axis)
    DepthSpan = ReadSignedSpan(Features[-1], Parameters) if Reverse else None
    Geometry, BodyValue = ProjectBody(
        Context, Shape, Material.id, DepthSpan, FrameValue
    )
    Title = dict(Model.Asset.Properties).get("documentName", "")
    Metadata: dict[str, object] = {
        "fusion.native_state": {"version": 2, "model": EncodeState(Model)}
    }
    if Rectangle is not None:
        Metadata["fusion.read_only"] = True
        if Rectangle.DisplayUnit is UnitSystem.KInch:
            Metadata["source_display_units"] = Rectangle.DisplayUnit.value
    Document = CadDocument(
        Source,
        (Configuration("default", Title, True),),
        Parameters,
        (SupportPlane(Context.Plane.Identity, "YZ" if YzDatum else "XY", FrameValue),),
        (ProjectSketch(Context, Shape, Rectangle),),
        (),
        Features,
        (BodyValue,),
        brep=Geometry,
        materials=(Material,),
        metadata=Metadata,
    )
    Document.AssertValid()
    return Document


# generic datum and reverse candidates must carry both independently typed geometry roles
def GenericStation(Model: DocumentModel, Context: ExtrudeContext) -> float:
    if (
        len(Model.Bodies) == 1
        and len(Model.Snapshots) == 1
        and isinstance(Model.Bodies[0].History, JournalModel)
        and isinstance(Model.Snapshots[0].Snapshot, GeometryState)
    ):
        return NumberValue(Context.Along.Fields["value"])
    return 0.0


# scoped generic and original rectangular body validation use their own stored geometry roles
def CheckPrismBody(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: RectGeometry,
    FrameValue: Transform,
    Reverse: bool,
    YzDatum: bool,
) -> None:
    if not (Reverse or YzDatum):
        CheckRegular(Graph, Context, Model, Shape)
        return
    History = Model.Bodies[0].History
    Snapshot = Model.Snapshots[0].Snapshot
    if not isinstance(History, JournalModel) or not isinstance(Snapshot, GeometryState):
        raise ValueError("Native generic prism requires its typed history and snapshot")
    if YzDatum:
        ReadDatumBody(Graph, Context, Model, Shape, History, Snapshot, FrameValue)
    else:
        SavedBody = ReadSignedBody(Context, Shape, History, Snapshot)
        CheckSignedTags(Graph, Context, Model, Shape, History, SavedBody)
    CheckSceneRefs(Graph, Model.Graphics)


# older typed rectangular history keeps its established semantics and attachment checks
def CheckRegular(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: RectGeometry,
) -> None:
    History = CheckBodyJoins(Graph, Context, Model)
    if not isinstance(History, PrismHistory):
        raise ValueError("Native rectangular extrusion requires prism history")
    CheckOperations(Graph, Context, History)
    CheckPrismTags(Graph, Context, Shape, History)
    CheckShape(Context, Shape, History)
    CheckMassCache(Context, History)
    CheckAuxiliary(Graph, Model, History)


# physical rebuilding uses the signed span of the actual projected driving parameter
def ReadSignedSpan(
    Feature: FeatureStep, Parameters: tuple[Parameter, ...]
) -> tuple[float, float]:
    Definition = Feature.definition
    if not isinstance(Definition, DistanceExtrude):
        raise ValueError("Native reverse prism requires a signed distance extrusion")
    Values = GetDistValues(
        Feature, Definition, {Value.id: Value for Value in Parameters}
    )
    if Values.LowerMm >= 0.0 or Values.UpperMm != 0.0:
        raise ValueError("Native reverse prism has inconsistent neutral signed extent")
    return Values.LowerMm, Values.UpperMm
