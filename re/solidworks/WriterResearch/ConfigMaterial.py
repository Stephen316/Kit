from math import isfinite as IsFinite

from ConfigRoot import KInitialNodeFlags
from ConfigSectionHatch import KHatchClass, KPartMaterial
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    KStringMarker,
    EncodeNull,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# material density has its own registered class and allocation
KDensityClass = "moDensityParameter_c"


# the next model data allocation belongs to the part after the material returns
KModelDataClass = "uoModelData_c"


# the initial density node remains unnamed and independent from feature identities
KDensityNodeState = (0, KInitialNodeFlags, -1, 0)


# nothing in this material profile changes the already assigned hatch slot
def RequireMaterialPos(
    Generation: int, NextIndex: int, Classes: dict[str, int]
) -> None:
    RequireArch(Generation, KConfigGen, "standalone part material generation")
    Hatch = Classes.get(KHatchClass, 0)
    RequireArch(
        Hatch in (47, 49)
        and NextIndex == Hatch + 2
        and not {KPartMaterial, KDensityClass, KModelDataClass}.intersection(Classes),
        True,
        "first material after the owned section hatch",
    )


# the standalone material requires a physical density supplied by the document caller
def RequireDensity(DensityKgM3: float) -> None:
    RequireArch(
        not isinstance(DensityKgM3, bool)
        and IsFinite(DensityKgM3)
        and DensityKgM3 > 0.0,
        True,
        "finite positive part density",
    )


# the density child adds its inline node fields without allocating optional names
def ReadConfigMaterial(Cursor: ArchiveCursor, Generation: int) -> float:
    Classes = {Name: Index for Index, Name in Cursor.Classes.items()}
    RequireMaterialPos(Generation, Cursor.NextIndex, Classes)
    Cursor.TakePointer((KPartMaterial,), KDefinitionKind, CompactOnly=True)
    Cursor.TakePointer((KDensityClass,), KDefinitionKind, CompactOnly=True)
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<iIiI"), KDensityNodeState, "unnamed density node state"
    )
    RequireArch(
        Cursor.BlobValue.startswith(KStringMarker, Cursor.Offset),
        True,
        "wide density node text",
    )
    RequireArch(Cursor.ReadText(), "", "empty density node text")
    Cursor.ReadNull()
    (Density,) = Cursor.ReadPoint(1)
    RequireDensity(Density)
    RequireArch(Cursor.ReadInts("<B"), (0,), "absent second density value")
    Next = ReadTag(Cursor.BlobValue, Cursor.Offset)
    RequireArch(
        (Next.kind, Next.class_name, Next.schema, Next.wide),
        (KDefinitionKind, KModelDataClass, 1, False),
        "next model data allocation after material",
    )
    return Density


# the material writer ends before the independently managed model data pointer
def WriteConfigMaterial(
    Writer: ArchiveWriter, Generation: int, DensityKgM3: float
) -> None:
    RequireMaterialPos(Generation, Writer.next_index, Writer.classes)
    RequireDensity(DensityKgM3)
    Writer.BeginObject(KPartMaterial, 1)
    Writer.BeginObject(KDensityClass, 1)
    Writer.raw(EncodeNull())
    Update, Flags, NodeId, FlagsTwo = KDensityNodeState
    Writer.i32(Update)
    Writer.u32(Flags)
    Writer.i32(NodeId)
    Writer.u32(FlagsTwo)
    Writer.string("")
    Writer.raw(EncodeNull())
    Writer.f64(DensityKgM3)
    Writer.u8(0)
