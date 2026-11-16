from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from CmgrInherited import (
    ArchiveFeature,
    CheckArcFeature,
    ReadArcFeature,
    WriteArcFeature,
)
from PrincipalPlaneAtom import ReadPrincipalAtom, WritePrincipalAtom
from PrincipalPlaneView import (
    KPrincipalFrames,
    PlaneView,
    PrincipalFrame,
    RequirePlaneView,
)
from ResolvedFolders import CheckFolderMap, KNameClass, WriteFolderName
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    EncodeNull,
    EncodeString,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPose
from convert.adapters.solidworks.Resolved.NamedNode import ReadNamedNode

# each principal datum consists of a named feature and its own default definition
KPlaneClass = "moRefPlane_c"


# a default data object is allocated separately for each principal plane
KDefaultData = "moDefaultRefPlnData_c"


# the standard order also defines the three default tree identities
KPlaneNames = ("Front Plane", "Top Plane", "Right Plane")


# principal nodes preserve the additional feature bit through the base node serializer
KPlaneFlags = 0xC0000000


# the canonical frames are centered around the part origin at unit scale
KUnitPose = (0.0, 0.0, 0.0, 1.0)


# saved display geometry and version state come from separate part owners
@Dataclass(frozen=True, slots=True)
class PrincipalPlane:
    Name: str
    TreeId: int
    Feature: ArchiveFeature
    View: PlaneView


# default data keeps the plane equation distinct from its derived display root
def ReadPlaneView(Cursor: ArchiveCursor, Kind: str, Frame: PrincipalFrame) -> PlaneView:
    NamePoint = Cursor.ReadPoint(3)
    RequireArch(Cursor.ReadInts("<2i"), (5, 0), "principal geometry mode and flag")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<i"), (0,), "principal reference state")
    Cursor.TakePointer((KDefaultData,), Kind, CompactOnly=True)
    RequireArch(Cursor.ReadPoint(3), (0.0, 0.0, 0.0), "default plane geometric origin")
    RequireArch(Cursor.ReadPoint(3), Frame.Normal, "default plane world normal")
    RequireArch(
        ReadLocalPose(Cursor), (Frame.Basis, KUnitPose), "default plane transform"
    )
    Border = Cursor.ReadPoint(4)
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<3iB"), (0, -4, -4, 0), "default plane border state")
    Root = Cursor.ReadPoint(3)
    RequireArch(Cursor.ReadInts("<2iH"), (1, 0, 0), "default plane display return")
    for _ in range(3):
        Cursor.ReadNull()
    View = PlaneView(NamePoint, Border, Root)
    RequirePlaneView(View)
    return View


# the codec keeps all three independent datums in the resolved archive namespace
def ReadResolvedPlanes(
    Cursor: ArchiveCursor, Generation: int
) -> tuple[PrincipalPlane, ...]:
    RequireArch(Generation, 19000, "resolved default plane generation")
    Planes = []
    for Offset, (Name, Frame) in enumerate(
        zip(KPlaneNames, KPrincipalFrames, strict=True)
    ):
        Kind = KDefinitionKind if Offset == 0 else KClassRefKind
        Cursor.TakePointer((KPlaneClass,), Kind, CompactOnly=True)
        Cursor.TakePointer((KNameClass,), KClassRefKind, CompactOnly=True)
        NameValue, TreeId = ReadNamedNode(Cursor, (KPlaneFlags,))
        RequireArch((NameValue, TreeId), (Name, Offset + 2), "principal tree identity")
        RequireArch(Cursor.ReadInts("<Hi"), (0, 0), "empty principal node list")
        Feature = ReadArcFeature(Cursor, Generation)
        ReadPrincipalAtom(Cursor)
        Planes.append(
            PrincipalPlane(
                NameValue, TreeId, Feature, ReadPlaneView(Cursor, Kind, Frame)
            )
        )
    Next = ReadTag(Cursor.BlobValue, Cursor.Offset)
    RequireArch(
        (Next.class_name, Next.kind, Next.schema, Next.wide),
        ("moOriginProfileFeature_c", KDefinitionKind, 1, False),
        "origin immediately after principal datums",
    )
    return tuple(Planes)


# writing the pose omits the basis only when its default identity is known
def WritePlaneView(
    Writer: ArchiveWriter, Frame: PrincipalFrame, View: PlaneView
) -> None:
    Writer.raw(PackFields("<3d2i", *View.NamePoint, 5, 0))
    Writer.raw(EncodeNull())
    Writer.i32(0)
    Writer.BeginObject(KDefaultData, 1)
    Writer.raw(PackFields("<6d", 0.0, 0.0, 0.0, *Frame.Normal))
    Writer.u8(int(Frame.Basis is not None))
    if Frame.Basis is not None:
        Writer.raw(PackFields("<9d", *Frame.Basis))
    Writer.raw(PackFields("<4dB4d", *KUnitPose, 0, *View.Border))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<3iB3d2iH", 0, -4, -4, 0, *View.DisplayRoot, 1, 0, 0))
    for _ in range(3):
        Writer.raw(EncodeNull())


# prepare all principal records before the first new class changes the live map
def WriteResolvedPlanes(
    Writer: ArchiveWriter, Generation: int, Planes: tuple[PrincipalPlane, ...]
) -> None:
    RequireArch(Generation, 19000, "resolved default plane generation")
    RequireArch(
        tuple((Plane.Name, Plane.TreeId) for Plane in Planes),
        tuple(zip(KPlaneNames, range(2, 5), strict=True)),
        "principal identities from the document graph",
    )
    CheckFolderMap(Writer, (KPlaneClass, KDefaultData), 11)
    Names = tuple(EncodeString(Plane.Name) for Plane in Planes)
    for Plane in Planes:
        CheckArcFeature(Generation, Plane.Feature)
        RequirePlaneView(Plane.View)
    for Name, Frame, Plane in zip(Names, KPrincipalFrames, Planes, strict=True):
        Writer.BeginObject(KPlaneClass, 1)
        WriteFolderName(Writer, Name, Plane.TreeId, Flags=KPlaneFlags)
        Writer.u16(0)
        Writer.i32(0)
        WriteArcFeature(Writer, Generation, Plane.Feature)
        WritePrincipalAtom(Writer)
        WritePlaneView(Writer, Frame, Plane.View)
