from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from AuthoredProfile import KSketchClass
from LocalComponent import CheckLocalComponent, WriteLocalComponent
from LocalPoint import WritePointEnd, WritePointOpen, WritePointPose
from OriginSketch import KPointHandle
from PartArchive import PartArchiveWriter
from RectangleCorners import KCornerMask, KLineHandle, KMemberStatus
from ResolvedOrigin import KOriginClass, KOriginName, KOriginTreeId
from convert.adapters.solidworks.Container.Archive import KBigObjectTag, EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KExtEntity = "sgExtEnt_c"
KSketchWrapper = "moSketchExtRef_w"
KCompHandle = "moCompSketchEntHandle_c"
KPointBackup = "moPointBackedUpData_c"
KProxyClasses = (KExtEntity, KSketchWrapper, KCompHandle, KPointBackup)


# the archive map and the document ghost ID live in different identity spaces
@Dataclass(frozen=True, slots=True)
class OriginProxy:
    FeatureObject: int
    FeatureId: int
    SketchObject: int
    PartObject: int
    GhostBodyId: int
    FeatureTime: int
    LastAccessStamp: int
    Position: tuple[float, float]


# the generated point handle targets the existing Origin rather than the coincident corner
def CheckOriginProxy(
    Writer: PartArchiveWriter, Generation: int, Sketch: int, Source: OriginProxy
) -> None:
    CheckLocalComponent(
        Writer, Generation, Source.PartObject, GhostBodyId=Source.GhostBodyId
    )
    RequireArch(
        Writer.objects.get(Source.FeatureObject) == KOriginClass
        and Source.FeatureId == KOriginTreeId
        and Writer.objects.get(Source.SketchObject) == KSketchClass
        and Source.FeatureObject < Source.SketchObject < Sketch < Writer.next_index
        and Writer.objects.get(Sketch) == KSketchClass,
        True,
        "distinct authored and Origin sketch objects",
    )
    RequireArch(
        Source.GhostBodyId > 0
        and type(Source.FeatureTime) is int
        and 0 < Source.FeatureTime < 0xFFFFFFFF
        and type(Source.LastAccessStamp) is int
        and 0 <= Source.LastAccessStamp <= 0x7FFFFFFF,
        True,
        "sketch-point ghost and compact initial reference state",
    )
    RequireArch(Source.Position, (0.0, 0.0), "ordinary local Origin point")
    RequireArch(
        all(Name in Writer.classes for Name in (KPointHandle, KLineHandle))
        and all(Name not in Writer.classes for Name in KProxyClasses)
        and Writer.next_index == Sketch + 10
        and Writer.next_index <= KBigObjectTag - 10,
        True,
        "proxy follows the four local corners in the shared map",
    )


# the wrapper's last access stamp and original feature time come from their own owners
def WriteProxyOwner(
    Writer: PartArchiveWriter, Generation: int, Source: OriginProxy
) -> None:
    Writer.BeginObject(KExtEntity, 1)
    Writer.BeginObject(KSketchWrapper, 1)
    Writer.BeginObject(KCompHandle, 1)
    WriteLocalComponent(
        Writer, Generation, Source.PartObject, GhostBodyId=Source.GhostBodyId
    )
    Writer.i32(Source.FeatureId)
    Writer.u32(Source.FeatureTime)
    Writer.BeginObject(KPointHandle, 1)
    Writer.raw(PackFields("<H2iI", 0, -1, 0, 1))
    Writer.u16(0)
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<2i2H", 0, Source.LastAccessStamp, 0, 0))
    Writer.raw(
        PackFields("<11ih", 0, 0, -12345, -12345, -12345, 0, Generation, 0, 0, 0, -1, 0)
    )
    Writer.BeginObject(KPointBackup, 1)
    Writer.raw(PackFields("<3d", *Source.Position, 0.0))
    for _ in range(3):
        Writer.raw(EncodeNull())
    Writer.string(f"Point1@{KOriginName}")


# a separate external point preserves the one Origin incidence without adding an edge
def WriteOriginProxy(
    Writer: PartArchiveWriter, Generation: int, Sketch: int, Source: OriginProxy
) -> None:
    CheckOriginProxy(Writer, Generation, Sketch, Source)
    WritePointOpen(Writer, 1, 5, 1, KMemberStatus)
    WriteProxyOwner(Writer, Generation, Source)
    WritePointPose(Writer, Source.Position, KCornerMask, 6, 0)
    Writer.raw(EncodeNull())
    Writer.raw(EncodeNull())
    WritePointEnd(Writer)
