from dataclasses import dataclass as Dataclass

from AuthoredProfile import AuthoredProfile, WriteAuthoredOpen
from ConfigHistory import ConfigHistory
from Display.Compose import DisplayDraft
from OriginProxy import OriginProxy, WriteOriginProxy
from PartArchive import PartArchiveWriter
from RectDimDisplay import WriteRectDisplays
from RectDisplayPose import SketchDisplayPose
from RectangleAnchor import KAnchorSlots, WriteRectAnchor
from RectangleAxes import WriteRectAxes
from RectangleCorners import KCornerMask, KMemberStatus, CornerPoint, WriteRectCorners
from RectangleDims import RectangleLength, WriteRectDims
from RectangleLines import RectangleLine, WriteRectLines
from RectangleRegion import CheckRectOutline, SketchRegionState, WriteRectRegion
from RectangleSupport import WriteProfileChain, WriteProfileSupport
from RectangleTrim import RectTrimState, WriteRectTrim
from Resolved.EndMap import EncodeResolvedEnd
from ResolvedOrigin import KOriginTreeId, OriginSlots
from convert.adapters.solidworks.Config.RootLayout import KRootClass
from convert.adapters.solidworks.Resolved.ContourSurf import ProfileOwner


@Dataclass(frozen=True, slots=True)
class ProfileDisplay:
    Poses: tuple[SketchDisplayPose, SketchDisplayPose]
    Draft: DisplayDraft
    Restored: bool


@Dataclass(frozen=True, slots=True)
class ProfileAttachment:
    DatumId: int
    DatumTime: int
    OriginTime: int
    OriginAccess: int


@Dataclass(frozen=True, slots=True)
class OrdinaryProfile:
    Feature: AuthoredProfile
    Corners: tuple[CornerPoint, ...]
    Lines: tuple[RectangleLine, ...]
    Lengths: tuple[RectangleLength, RectangleLength]
    AxisOrder: tuple[int, ...]
    Display: ProfileDisplay
    Region: SketchRegionState
    Attachment: ProfileAttachment
    Trim: RectTrimState


@Dataclass(frozen=True, slots=True)
class OrdinaryProfileSlots:
    Feature: int
    Sketch: int
    File: int


# The graph drives both the authored sketch and the later trimmed surface.
def WriteOrdinaryProfile(
    Writer: PartArchiveWriter,
    Generation: int,
    History: ConfigHistory,
    Origin: OriginSlots,
    State: OrdinaryProfile,
) -> OrdinaryProfileSlots:
    (Part,) = (Index for Index, Name in Writer.objects.items() if Name == KRootClass)
    Edges = {Line.CreationId: Line.Endpoints for Line in State.Lines}
    CheckRectOutline(Edges, tuple(Member.EdgeId for Member in State.Trim.Members))
    Corners = tuple(Corner.Position for Corner in State.Corners)
    Profile = WriteAuthoredOpen(
        Writer, Generation, Origin.SketchObject, State.Feature, len(Corners) + 1
    )
    Proxy = OriginProxy(
        Origin.FeatureObject,
        KOriginTreeId,
        Origin.SketchObject,
        Part,
        History.GhostRelation.GhostId,
        State.Attachment.OriginTime,
        State.Attachment.OriginAccess,
        (0.0, 0.0),
    )
    WriteRectCorners(
        Writer,
        Generation,
        Profile.Sketch,
        State.Corners,
        Edges,
        Mask=KCornerMask,
        Status=KMemberStatus,
    )
    WriteOriginProxy(Writer, Generation, Profile.Sketch, Proxy)
    WriteRectLines(Writer, Generation, Profile.Sketch, State.Lines)
    Distances = WriteRectDims(
        Writer, Generation, Profile.Sketch, Corners, State.Lengths
    )
    WriteRectAxes(Writer, Generation, Profile.Sketch, Corners, Edges, State.AxisOrder)
    WriteRectAnchor(
        Writer, Generation, Profile.Sketch, (*Corners, Proxy.Position), KAnchorSlots
    )
    WriteRectDisplays(
        Writer,
        Generation,
        Profile.Sketch,
        Distances,
        Corners,
        State.Lengths,
        State.Display.Poses,
        State.Display.Draft,
        Restored=State.Display.Restored,
    )
    WriteRectRegion(Writer, Generation, Profile.Sketch, Edges, State.Region)
    HasBoss = History.Atom is not None
    WriteProfileChain(Writer, tuple(sorted(Edges)) if HasBoss else None)
    WriteProfileSupport(
        Writer, Generation, Part, State.Attachment.DatumId, State.Attachment.DatumTime
    )
    Owner: ProfileOwner = {
        "profile_object": Profile.Profile,
        "native_feature_id": State.Feature.TreeId,
    }
    File = WriteRectTrim(
        Writer, Generation, Owner, tuple(Edges), int(HasBoss), State.Trim
    )
    if not HasBoss:
        Writer.raw(EncodeResolvedEnd(Generation=Generation, EntryCount=18))
    return OrdinaryProfileSlots(Profile.Profile, Profile.Sketch, File)
