from dataclasses import dataclass as Dataclass
from math import hypot, isfinite

from AuthoredProfile import KNodeFlags, AuthoredProfile
from BlindDimension import KRetainCount, DimGeometry, RequireFrame
from BossChoice import BossChoiceState
from BossInput import LogicalBoss
from BossOpen import KBossFlags, BossOpening
from BossProfile import KFrontAxes, Axes, KPoint, LocalProfile
from BossResolve import ResolvedBossState
from BossRules import BoundSize
from CmgrExternal import RequireExtState
from CmgrInherited import ArchiveFeature, CheckArcFeature
from ConfigAtomManager import BossAtomBody, RequireBossBody
from Display.Compose import BossDisplay, DisplayDraft
from HeaderLogs import KDefaultIds, KMaxTreeId
from HeaderTail import BoundPoints, FrameValues, HeaderBounds, Point
from OrdinaryProfile import OrdinaryProfile, ProfileAttachment, ProfileDisplay
from RectDisplayPose import SketchDisplayPose
from RectangleDims import RectangleLength, RectLengthSlots
from RectangleLines import KPermMarkOrders, RectangleLine
from RectangleRegion import CheckRectOutline, SketchRegionState
from RectangleSupport import KProfileAxes
from RectangleTrim import RectTrimState
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# feature allocation and dimension identifiers come from the target, alongside its clocks
@Dataclass(frozen=True, slots=True, kw_only=True)
class BossIds:
    Profile: int
    Operation: int
    Width: int
    Height: int
    Depth: int


# the length chooses its own local direction while text placement remains independent
@Dataclass(frozen=True, slots=True, kw_only=True)
class SizePose:
    TextWorld: Point
    TextRatio: float
    WitnessMetres: float


# drafted rectangle settings have no authoritative source in the logical sketch graph
@Dataclass(frozen=True, slots=True, kw_only=True)
class ProfileWire:
    Feature: ArchiveFeature
    NodeFlags: int
    PermanentMarks: tuple[int, ...]
    AxisOrder: tuple[int, ...]
    Poses: tuple[SizePose, SizePose]
    Draft: DisplayDraft
    Restored: bool
    Region: SketchRegionState
    DatumTime: int
    OriginTime: int
    OriginAccess: int
    Trim: RectTrimState


# call out independent annotation choices while binding their geometry to actual corners
@Dataclass(frozen=True, slots=True, kw_only=True)
class BossPose:
    AnchorSlot: int
    TangentEdge: int
    FlipTangent: bool
    Basis: tuple[SpaceVector, SpaceVector, SpaceVector]
    WitnessMetres: float


# kernel labels and ordered native cap traversals remain explicit inputs
@Dataclass(frozen=True, slots=True, kw_only=True)
class BossWire:
    Feature: ArchiveFeature
    NodeFlags: int
    SolidBodyTag: int
    PartitionMarkId: int
    ReferenceTime: int
    CapOrders: tuple[tuple[int, ...], tuple[int, ...]]
    Pose: BossPose
    Draft: DisplayDraft


# the same atom supplies the boss identity and the same box feeds all enclosing writers
@Dataclass(frozen=True, slots=True)
class BossWriterInput:
    Profile: OrdinaryProfile
    Boss: ResolvedBossState
    Atom: BossAtomBody
    Bounds: HeaderBounds
    DisplacementMm: Point


# exact point slots are checked against the dimension writer's own lookup
def BindLength(
    Corners: tuple[KPoint, ...], Bound: BoundSize, Identity: int, Pose: SizePose
) -> tuple[RectangleLength, SketchDisplayPose]:
    Length = RectangleLength(Bound.Length.Name, Identity, Bound.Length.Millimetres)
    Metres = Length.Millimetres / 1000.0
    RequireArch(
        RectLengthSlots(Corners, Metres), Bound.PointSlots, "owned size operands"
    )
    XValue, YValue = Corners[Bound.PointSlots[1]]
    return Length, SketchDisplayPose(
        Pose.TextWorld,
        Pose.TextRatio,
        Pose.WitnessMetres,
        (XValue / Metres, YValue / Metres, 0.0),
    )


# map the logical plane coordinates to world millimetres before applying signed depth
def WorldPoint(Profile: LocalProfile, PointValue: KPoint) -> Point:
    Frame = Profile.Plane
    First, Second = PointValue
    XValue, YValue, ZValue = (
        Origin + First * UAxis + Second * VAxis
        for Origin, UAxis, VAxis in zip(
            Axes(Frame.origin), Axes(Frame.x_axis), Axes(Frame.y_axis), strict=True
        )
    )
    return XValue, YValue, ZValue


# the evaluated start and generated end points share one native-unit bound
def BossBounds(Corners: tuple[Point, ...], Displacement: Point) -> HeaderBounds:
    DX, DY, DZ = Displacement
    Points = tuple(
        ((XValue + EndX) / 1000.0, (YValue + EndY) / 1000.0, (ZValue + EndZ) / 1000.0)
        for XValue, YValue, ZValue in Corners
        for EndX, EndY, EndZ in ((0.0, 0.0, 0.0), (DX, DY, DZ))
    )
    return BoundPoints(Points)


# the annotation references an actual base corner and one oriented owned line
def BindBossPose(
    Logical: LogicalBoss, Corners: tuple[Point, ...], Pose: BossPose
) -> DimGeometry:
    Edges = Logical.Profile.EdgeSlots
    RequireArch(
        type(Pose.AnchorSlot) is int
        and 0 <= Pose.AnchorSlot < len(Corners)
        and type(Pose.TangentEdge) is int
        and Pose.TangentEdge in Edges
        and type(Pose.FlipTangent) is bool,
        True,
        "boss annotation corner and edge roles",
    )
    FirstAxis, SecondAxis, NormalAxis = Pose.Basis
    Basis = Axes(FirstAxis), Axes(SecondAxis), Axes(NormalAxis)
    RequireFrame(Basis)
    RequireArch(Basis == KFrontAxes, False, "explicit dimension pose matrix")
    RequireArch(isfinite(Pose.WitnessMetres), True, "finite boss dimension witness")
    First, Second = Edges[Pose.TangentEdge]
    Delta = tuple(
        (End - Start) * (-1.0 if Pose.FlipTangent else 1.0)
        for Start, End in zip(Corners[First], Corners[Second], strict=True)
    )
    Magnitude = hypot(*Delta)
    TX, TY, TZ = (Value / Magnitude for Value in Delta)
    return DimGeometry(
        Transform(SpaceVector(*Corners[Pose.AnchorSlot]), *Pose.Basis),
        Logical.Profile.Plane.z_axis,
        SpaceVector(TX, TY, TZ),
        Logical.Reversed,
    )


# feature and relation IDs use their respective native namespaces
def CheckBossIds(Ids: BossIds) -> None:
    RequireArch(
        Ids.Profile != Ids.Operation
        and all(
            type(Value) is int and 0 < Value <= KMaxTreeId and Value not in KDefaultIds
            for Value in (Ids.Profile, Ids.Operation)
        ),
        True,
        "two unreserved native feature identities",
    )
    RequireArch(
        Ids.Width != Ids.Height
        and all(
            type(Value) is int and 0 < Value <= KMaxTreeId
            for Value in (Ids.Width, Ids.Height)
        )
        and type(Ids.Depth) is int
        and 0 <= Ids.Depth <= KMaxTreeId,
        True,
        "independent native sketch and boss dimension identities",
    )


# build the ordinary profile from bound corner, line and distance operands
def BindProfile(
    Logical: LogicalBoss, Ids: BossIds, State: ProfileWire
) -> OrdinaryProfile:
    Edges = Logical.Profile.EdgeSlots
    CheckArchProfile(Logical, State)
    Lines = tuple(
        RectangleLine(Mark, Edge.Identity, Edge.PointSlots, 1)
        for Mark, Edge in zip(State.PermanentMarks, Logical.Profile.Edges, strict=True)
    )
    Corners = Logical.Profile.CornersMetres
    Width, WidthPose = BindLength(Corners, Logical.Width, Ids.Width, State.Poses[0])
    Height, HeightPose = BindLength(Corners, Logical.Height, Ids.Height, State.Poses[1])
    (Datum,) = (
        Id for Id, Axis in KProfileAxes.items() if Axis == Logical.Profile.AxisCode
    )
    CheckRectOutline(Edges, State.Region.Outline)
    CheckRectOutline(Edges, tuple(Member.EdgeId for Member in State.Trim.Members))
    return OrdinaryProfile(
        AuthoredProfile(
            Logical.SketchName, Ids.Profile, State.NodeFlags, State.Feature
        ),
        Logical.Corners,
        Lines,
        (Width, Height),
        State.AxisOrder,
        ProfileDisplay((WidthPose, HeightPose), State.Draft, State.Restored),
        State.Region,
        ProfileAttachment(Datum, State.DatumTime, State.OriginTime, State.OriginAccess),
        State.Trim,
    )


# preserve independent capture-style settings only within the target writer's known profile
def CheckArchProfile(Logical: LogicalBoss, State: ProfileWire) -> None:
    CheckArcFeature(KConfigGen, State.Feature, AllowRegenTime=True)
    RequireArch(State.NodeFlags in KNodeFlags, True, "ordinary profile node flags")
    RequireArch(
        State.PermanentMarks in KPermMarkOrders, True, "witnessed permanent marks"
    )
    RequireArch(
        (len(State.AxisOrder), set(State.AxisOrder)),
        (4, set(Logical.Profile.EdgeSlots)),
        "one saved axis entry per owned line",
    )
    RequireArch(
        State.Trim.File.ConfigName, Logical.ConfigurationName, "same trim configuration"
    )
    RequireArch(Logical.ConfigurationName, "Default", "standalone trim configuration")
    RequireExtState(State.Trim.File, SelfReference=False)


# one logical side controls projection, signed display geometry and the native end
def BindBossWriter(
    Logical: LogicalBoss, Ids: BossIds, Profile: ProfileWire, Boss: BossWire
) -> BossWriterInput:
    CheckBossIds(Ids)
    CheckArcFeature(KConfigGen, Boss.Feature, AllowRegenTime=True)
    RequireArch(Boss.NodeFlags in KBossFlags, True, "ordinary boss node flags")
    Atom = BossAtomBody(Ids.Operation, Boss.SolidBodyTag)
    RequireBossBody(Atom)
    RequireArch(
        type(Boss.PartitionMarkId) is int and 0 < Boss.PartitionMarkId <= KMaxTreeId,
        True,
        "explicit native partition mark",
    )
    for Order in Boss.CapOrders:
        CheckRectOutline(Logical.Profile.EdgeSlots, Order)
    Corners = tuple(
        WorldPoint(Logical.Profile, Value) for Value in Logical.Profile.CornersMm
    )
    NX, NY, NZ = Axes(Logical.Profile.Plane.z_axis)
    Depth = Logical.Depth.Millimetres
    Displacement = (NX * Depth, NY * Depth, NZ * Depth)
    Bounds = BossBounds(Corners, Displacement)
    ProfileInput = BindProfile(Logical, Ids, Profile)
    CX, CY, CZ, *_, Radius = FrameValues(Bounds)
    Choice = BossChoiceState(
        Boss.ReferenceTime,
        Boss.CapOrders,
        (CX, CY, CZ),
        2 * Radius,
    )
    Display = BossDisplay(
        DimensionId=Ids.Depth,
        RetainCount=KRetainCount,
        NameValue=Logical.Depth.Name,
        DepthMm=Logical.MagnitudeMm,
        Geometry=BindBossPose(Logical, Corners, Boss.Pose),
        WitnessMetres=Boss.Pose.WitnessMetres,
    )
    End = ResolvedBossState(
        BossOpening(Logical.FeatureName, Boss.NodeFlags, Boss.Feature),
        Choice,
        Boss.PartitionMarkId,
        Display,
        Boss.Draft,
    )
    return BossWriterInput(ProfileInput, End, Atom, Bounds, Displacement)
