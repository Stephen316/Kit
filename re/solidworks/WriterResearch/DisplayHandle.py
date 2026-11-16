from struct import pack as PackFields

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    KMaxMapIndex,
    EncodeNull,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter
from convert.adapters.solidworks.Resolved.BossDepth import FeatureHandle, ReadFeatHandle
from convert.adapters.solidworks.Sketch.DimHandle import KEmptyDimPart

# the first native handle occurrence has an explicit compact class definition
KHandleClass = "moFeatureDimHandle_c"

# the witnessed runtime class has schema one in the plain part archive
KHandleSchema = 1

# the component store distinguishes two unsigned words from its signed presence fields
KComponentFormat = "<8iIi4i5iI"

# the local handle initializer clears both transform pointers before writing
KAbsentTransform = 0

# each native view tag slot is null on the witnessed part handle
KViewTagCount = 4

# a local feature handle starts without either optional reference pointer
KOptionalRefCount = 2

# the reference serializer writes its constructor route byte before those pointers
KLocalRoute = 0

# the signed route default precedes the independent dimension archive identity
KDefaultRouteState = -1

# the handle initializer clears the signed route flags before archive storage
KDefaultRouteFlags = 0


# the plain first definition needs room for its own class and object slots
def RequireScope(Generation: int, ConditionOne: bool, NextIndex: int) -> None:
    RequireArch(
        (Generation, ConditionOne), (KConfigGen, False), "plain modern feature handle"
    )
    RequireArch(1 <= NextIndex < KMaxMapIndex, True, "feature handle allocation range")


# the inherited component and reference defaults end before the owned dimension tag
def WriteHandleMut(
    Writer: ArchiveWriter, *, Generation: int, ConditionOne: bool
) -> int:
    RequireScope(Generation, ConditionOne, Writer.next_index)
    RequireArch(KHandleClass in Writer.classes, False, "first feature handle class")
    ObjectIndex = Writer.next_index + 1
    Writer.begin_object(KHandleClass, KHandleSchema)
    Writer.raw(EncodeEmptyHandle(Generation))
    return ObjectIndex


# both typed handle subclasses start with the same absent component and transforms
def EncodeEmptyHandle(Generation: int) -> bytes:
    NullValue = EncodeNull()
    return (
        NullValue
        + PackFields(KComponentFormat, *KEmptyDimPart[:-1], Generation)
        + PackFields("<H", KAbsentTransform)
        + NullValue * KViewTagCount
        + PackFields("<B", KLocalRoute)
        + NullValue * KOptionalRefCount
        + PackFields("<iHi", KDefaultRouteState, KAbsentTransform, KDefaultRouteFlags)
    )


# invalid inherited fields must leave the caller offset and allocation maps intact
def ReadHandleMut(
    Parent: ArchiveCursor, *, Generation: int, ConditionOne: bool
) -> FeatureHandle:
    RequireScope(Generation, ConditionOne, Parent.NextIndex)
    RequireArch(
        KHandleClass in Parent.Classes.values(), False, "first feature handle class"
    )
    Cursor = ArchiveCursor(
        Parent.BlobValue,
        Parent.Offset,
        Parent.NextIndex,
        Parent.Classes.copy(),
        Parent.Objects.copy(),
    )
    if Parent.PointerEvents is not None:
        Cursor.PointerEvents = []
    Handle = ReadFeatHandle(Cursor, KDefinitionKind)
    Parent.Offset, Parent.NextIndex = Cursor.Offset, Cursor.NextIndex
    Parent.Classes.update(Cursor.Classes)
    Parent.Objects.update(Cursor.Objects)
    if Parent.PointerEvents is not None and Cursor.PointerEvents is not None:
        Parent.PointerEvents.extend(Cursor.PointerEvents)
    return Handle
