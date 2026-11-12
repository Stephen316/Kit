from collections.abc import Mapping
from xml.etree.ElementTree import Element
from zipfile import ZipFile, ZipInfo

from convert.adapters.freecad.EditAxisRev.ApplyAxisRevEdit import ApplyAxisRevEdit
from convert.adapters.freecad.EditAxisRev.AxisReadCache import CheckAxisCaches
from convert.adapters.freecad.EditAxisRev.AxisReadGraph import AxisGraph, ReadAxisGraph
from convert.adapters.freecad.EditAxisRev.AxisReadPose import (
    CheckAxisExpr,
    CheckAxisLink,
    CheckAxisPose,
)
from convert.adapters.freecad.EditAxisRev.AxisReadSketch import (
    ReadAxisGuide,
    ReadAxisSketch,
)
from convert.adapters.freecad.EditAxisRev.AxisRevExpr import AxisAngleExpr
from convert.adapters.freecad.EditAxisRev.AxisRevPlan import AxisRevPlan, ReadAxisRev
from convert.adapters.freecad.EditRead.Revolve.RevSheet import ReadRevSheet
from convert.adapters.freecad.EditRev.RevCacheProof import CheckRevSolid
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import KOriginZero


# older exports are equivalent only when native normalization cannot scale a translation
def AxisReadExprs(
    Graph: AxisGraph,
    PlanValue: AxisRevPlan,
    Profile: Sketch,
    AxisIndex: int,
    Alias: str,
    IsSeed: bool,
) -> tuple[str, ...]:
    Expected = Graph.Template[Graph.Feature.name].properties["ExpressionEngine"][0][0]
    Result: tuple[str, ...] = (Expected.attrib["expression"],)
    Members = set(Profile.closed_profile_entity_ids[0])
    Lines = tuple(
        Index for Index, Value in enumerate(Profile.entities) if Value.id in Members
    )
    Arguments = (
        Graph.AxisSketch.name,
        AxisIndex,
        Graph.Profile.name,
        Lines,
        f"Parameters.{Alias}",
    )
    if IsSeed or PlanValue.ProfileFrame.origin == KOriginZero:
        Result += (AxisAngleExpr(*Arguments, MeanStyle="legacy"),)
    if PlanValue.ProfileFrame.origin == KOriginZero:
        Result += (AxisAngleExpr(*Arguments, MeanStyle="saved"),)
    return Result


# the saved solid must independently agree with both edited input sketches and the live angle
def ReconcileAxis(
    DocValue: CadDocument,
    Manifest: Mapping[str, object],
    RootValue: Element,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    Binding: str,
) -> CadDocument:
    Feature = DocValue.feature_timeline[-1] if DocValue.feature_timeline else None
    PlanValue = (
        ReadAxisRev(DocValue, Feature) if Feature and Binding == Feature.id else None
    )
    if PlanValue is None:
        raise ValueError(
            "FreeCAD editable sketch axis binding disagrees with its source"
        )
    Graph = ReadAxisGraph(RootValue, Manifest, DocValue, PlanValue)
    ByIdentity = {Value.id: Value for Value in DocValue.sketches}
    Original = ByIdentity[PlanValue.Revolve.SketchId]
    OriginalAxis = ByIdentity[PlanValue.AxisSketchId]
    Profile = ReadAxisSketch(
        Graph.Profile, Graph.Template[Graph.Profile.name], Original
    )
    AxisSketch = ReadAxisSketch(
        Graph.AxisSketch, Graph.Template[Graph.AxisSketch.name], OriginalAxis, 1
    )
    Guide = ReadAxisGuide(Graph.AxisSketch, OriginalAxis, AxisSketch, PlanValue)
    Shape, IsSeed = CheckAxisCaches(
        Archive, Members, Graph, PlanValue, Original, Profile, AxisSketch, Guide
    )
    Aliases, Along, _, AlongText, _ = ReadRevSheet(
        Graph.ParamSheet, DocValue.parameters, PlanValue.Revolve
    )
    AxisIndex = len(OriginalAxis.entities)
    CheckAxisLink(Graph.Feature, Graph.AxisSketch.name, AxisIndex + 1, IsSeed)
    CheckAxisExpr(
        Graph.Feature,
        AxisReadExprs(
            Graph,
            PlanValue,
            Profile,
            AxisIndex,
            Aliases[PlanValue.Revolve.AngleParamId],
            IsSeed,
        ),
    )
    Rebuilt = ApplyAxisRevEdit(
        DocValue, PlanValue, Profile, AxisSketch, (Along, AlongText)
    )
    if IsSeed and Rebuilt is not DocValue:
        raise ValueError(
            "FreeCAD editable sketch axis edit is missing its saved sketch caches"
        )
    Definition = Rebuilt.feature_timeline[-1].definition
    if not isinstance(Guide.geometry, LineGeometry) or not isinstance(
        Definition, AngularRevolve
    ):
        raise ValueError("FreeCAD editable sketch axis geometry is unresolved")
    CheckAxisPose(
        Graph.Feature,
        Guide.geometry,
        PlanValue.AxisFrame,
        Definition.AxisDirection,
        Along,
        IsSeed,
    )
    CheckRevSolid(Archive, Members, Shape, Rebuilt)
    return Rebuilt
