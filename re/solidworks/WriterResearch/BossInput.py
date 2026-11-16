from collections import Counter
from dataclasses import dataclass as Dataclass

from BossProfile import Axes, LocalProfile, ReadLocalProfile
from BossRules import BoundSize, DrivingLength, ReadDrivingLength, ReadRectRules
from RectangleCorners import CornerPoint
from convert.Commands.CheckFeatures import CheckFeatures
from convert.Commands.CheckRetained import CheckRetained
from convert.adapters.registry.SupportWrite import CheckSupports
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.document.Models.DocumentModel import CadDocument


# logical owners survive the conversion while target archive bookkeeping is assigned later
@Dataclass(frozen=True, slots=True)
class LogicalBoss:
    SketchFeatureId: str
    SketchName: str
    FeatureId: str
    FeatureName: str
    BodyId: str
    BodyName: str
    ConfigurationName: str
    Profile: LocalProfile
    Width: BoundSize
    Height: BoundSize
    Depth: DrivingLength

    @property
    def MagnitudeMm(self) -> float:
        return abs(self.Depth.Millimetres)

    @property
    def Reversed(self) -> bool:
        return self.Depth.Millimetres < 0

    @property
    def AxialBoundsMm(self) -> tuple[float, float]:
        Depth = self.Depth.Millimetres
        return min(0.0, Depth), max(0.0, Depth)

    @property
    def Corners(self) -> tuple[CornerPoint, ...]:
        Incidences = Counter((0, *self.Width.PointSlots, *self.Height.PointSlots))
        return tuple(
            CornerPoint(Index + 1, Point, Incidences[Index])
            for Index, Point in enumerate(self.Profile.CornersMetres)
        )


# shared portable guards cover retained payloads, qualified support, and dependency semantics
def CheckBossGraph(Document: CadDocument) -> None:
    CheckRetained(Document)
    RequireArch(
        Document.assembly is None
        and Document.brep is None
        and not Document.meshes
        and not Document.brep_payloads
        and not Document.materials
        and not Document.selections
        and Document.metadata.get("kit.research_read_status") != "unqualified"
        and Document.units == UnitSystem.KMillimeter,
        True,
        "ordinary metric standalone graph with feature history as geometry",
    )
    RequireArch(
        tuple(
            len(Values)
            for Values in (
                Document.configurations,
                Document.support_planes,
                Document.sketches,
                Document.feature_timeline,
                Document.bodies,
                Document.parameters,
            )
        ),
        (1, 1, 1, 2, 1, 3),
        "one configuration, datum, profile, solid and three driving lengths",
    )
    CheckSupports(Document)
    CheckFeatures(Document)


# this research projection supplies logical inputs only after proving the exact graph
def ProjectBoss(Document: CadDocument) -> LogicalBoss:
    CheckBossGraph(Document)
    (Config,), (Plane,), (Sketch,), (Body,) = (
        Document.configurations,
        Document.support_planes,
        Document.sketches,
        Document.bodies,
    )
    First, Boss = sorted(Document.feature_timeline, key=lambda Step: Step.order)
    RequireArch(
        Config.active
        and Config.parent_id is None
        and not Config.overrides
        and not Config.suppressed_feature_ids
        and bool(Config.name),
        True,
        "one active configuration without variant overrides",
    )
    RequireArch(
        not Sketch.suppressed
        and Sketch.support_plane_id == Plane.id
        and First.order < Boss.order
        and First.id != Boss.id
        and First.kind == FeatureKind.KReference
        and First.definition is None
        and First.operation is None
        and not First.input_feature_ids
        and Boss.sketch_id == First.sketch_id == Sketch.id
        and Boss.input_feature_ids == (First.id,)
        and Boss.kind == FeatureKind.KExtrusion
        and Boss.operation == BooleanOp.KCreate
        and Body.final_feature_id == Boss.id
        and Body.material_id is None
        and all(
            not Step.suppressed
            and not Step.configuration_states
            and not Step.selection_ids
            for Step in (First, Boss)
        )
        and all(
            Name and "\0" not in Name for Name in (Sketch.name, Boss.name, Body.name)
        ),
        True,
        "one active rectangle sketch directly creates the sole body",
    )
    Profile = ReadLocalProfile(Sketch, Plane)
    Parameters = {Item.id: Item for Item in Document.parameters}
    RequireArch(len(Parameters), 3, "three distinct parameter identities")
    Width, Height = ReadRectRules(Sketch, Profile, Parameters, First.id)
    RequireArch(
        len(First.parameter_ids) == 2
        and set(First.parameter_ids)
        == {Width.Length.ParameterId, Height.Length.ParameterId},
        True,
        "both width and height belong to the sketch feature",
    )
    Definition = Boss.definition
    if not isinstance(Definition, DistanceExtrude):
        raise ValueError("boss requires one portable linked distance extrusion")
    RequireArch(
        Definition.SideMode == "one_sided"
        and all(
            Value is None
            for Value in (
                Definition.AgainstParameterId,
                Definition.StartOffsetId,
                Definition.TaperParameterId,
                Definition.SecondTaperId,
            )
        )
        and Axes(Definition.Direction) == Axes(Profile.Plane.z_axis)
        and Boss.parameter_ids == (Definition.AlongParameterId,)
        and Definition.AlongParameterId in Parameters,
        True,
        "one sketch-normal blind driving distance without extra start or taper",
    )
    Depth = ReadDrivingLength(Parameters[Definition.AlongParameterId], Boss.id)
    RequireArch(Depth.Millimetres != 0, True, "nonzero signed boss depth")
    RequireArch(
        Depth.Name not in (Width.Length.Name, Height.Length.Name),
        True,
        "separately named driving depth",
    )
    return LogicalBoss(
        First.id,
        Sketch.name,
        Boss.id,
        Boss.name,
        Body.id,
        Body.name,
        Config.name,
        Profile,
        Width,
        Height,
        Depth,
    )
