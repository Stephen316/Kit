from ConfigUnitFields import (
    ConfigUnitState,
    ReadUnitFields,
    RequireUnitState,
    UnitDisplay,
    WriteUnitFields,
)
from convert.adapters.solidworks.Config.RootLayout import KConfigGen, KRootClass
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    EncodeNull,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import KNodeNameClass, KVisualClass
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# the table owns the native unit pointer array before the model component
KUnitTable = "moUnitsTable_c"


# both length formatters allocate under the same archive class definition
KLengthClass = "moLengthUserUnits_c"


# density appends member selectors and an optional child to the base formatter
KDensityClass = "moDensityUnits_c"


# the units array depends on the archive namespace left by the root visual object
KUnitPrelude = {KRootClass: 1, KNodeNameClass: 4, KVisualClass: 6}


# native default table creation establishes member order before units are configured
KUnitClasses = (
    KLengthClass,
    "moAngleUserUnits_c",
    "moNumberUserUnits_c",
    KDensityClass,
    "moFloatNumberUserUnits_c",
    "moSpringConstantUnits_c",
    "moUnitSysUnits_c",
    "moForceUnits_c",
    "moStressUnits_c",
    "moGravityUnits_c",
    "moLinearMotorUnits_c",
    "moRotaryMotorUnits_c",
    "moPowerUnits_c",
    "moEnergyUnits_c",
    "moTimeUnits_c",
    "moFrequencyUserUnits_c",
)


# the same units serve both writer and reader when checking class specific suffixes
KExtraUnits = {
    "moAngleUserUnits_c": 0,
    "moUnitSysUnits_c": 0,
    "moForceUnits_c": 0,
    "moPowerUnits_c": 0,
    "moEnergyUnits_c": 0,
    "moTimeUnits_c": 0,
}


# the second length unit is a separately allocated child using the first class slot
def ReadLengths(Cursor: ArchiveCursor) -> tuple[int, float]:
    Previous = ReadUnitFields(Cursor, "primary")
    (Length,) = Cursor.ReadInts("<H")
    Cursor.TakePointer((KLengthClass,), KClassRefKind, CompactOnly=True)
    RequireArch(ReadUnitFields(Cursor, "dual"), 0.0, "dual length formatter state")
    RequireArch(Cursor.ReadInts("<H"), (3,), "dual length unit enum")
    Cursor.ReadNull()
    return Length, Previous


# common formatters may append a derived selector or independent density settings
def ReadCommonUnit(Cursor: ArchiveCursor, Name: str) -> tuple[int, ...]:
    RequireArch(ReadUnitFields(Cursor, "common"), 0.0, f"{Name} formatter state")
    if Name == KDensityClass:
        Volume, Mass, Child, Legacy, UseLegacy = Cursor.ReadInts("<HHBHi")
        RequireArch(Child, 0, "density without an assigned length unit child")
        return (Volume, Mass, Legacy, UseLegacy)
    if Name in KExtraUnits:
        return Cursor.ReadInts("<H")
    return ()


# the actual allocations must remain visible to the enclosing model component
def ReadConfigUnits(Cursor: ArchiveCursor, Generation: int) -> ConfigUnitState:
    Classes = {Name: Index for Index, Name in Cursor.Classes.items()}
    RequireArch(
        (Generation, Cursor.NextIndex, Classes),
        (KConfigGen, 8, KUnitPrelude),
        "units after visual owner",
    )
    Cursor.TakePointer((KUnitTable,), KDefinitionKind, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<H"), (len(KUnitClasses),), "config unit array count")
    Cursor.TakePointer((KLengthClass,), KDefinitionKind, CompactOnly=True)
    Length, Previous = ReadLengths(Cursor)
    Suffixes: dict[str, tuple[int, ...]] = {}
    for Name in KUnitClasses[1:]:
        Cursor.TakePointer((Name,), KDefinitionKind, CompactOnly=True)
        Suffixes[Name] = ReadCommonUnit(Cursor, Name)
    for Name in ("moAngleUserUnits_c", "moPowerUnits_c", "moTimeUnits_c"):
        RequireArch(Suffixes[Name], (0,), f"{Name} measured selector")
    Volume, Mass, Legacy, UseLegacy = Suffixes[KDensityClass]
    Display = UnitDisplay(
        Length,
        Suffixes["moUnitSysUnits_c"][0],
        Suffixes["moForceUnits_c"][0],
        Suffixes["moEnergyUnits_c"][0],
        Volume,
        Mass,
        Legacy,
        UseLegacy,
    )
    State = ConfigUnitState(Display, Previous)
    RequireUnitState(Generation, State)
    return State


# unit registration must preserve the nested length allocation before other formatters
def WriteLengths(Writer: ArchiveWriter, State: ConfigUnitState) -> None:
    Writer.BeginObject(KLengthClass, 1)
    WriteUnitFields(Writer, "primary", State.PreviousLength)
    Writer.u16(State.Display.Length)
    Writer.BeginObject(KLengthClass, 1)
    WriteUnitFields(Writer, "dual")
    Writer.u16(3)
    Writer.raw(EncodeNull())


# writing density options needs the caller supplied mass and volume format members
def WriteDensity(Writer: ArchiveWriter, Display: UnitDisplay) -> None:
    Writer.u16(Display.DensityVolume)
    Writer.u16(Display.DensityMass)
    Writer.u8(0)
    Writer.u16(Display.LegacyVolume)
    Writer.i32(Display.UseLegacyVolume)


# the model continuation depends on the map allocated by this typed pointer table
def WriteConfigUnits(
    Writer: ArchiveWriter, Generation: int, State: ConfigUnitState
) -> None:
    RequireUnitState(Generation, State)
    RequireArch(
        (Writer.next_index, Writer.classes),
        (8, KUnitPrelude),
        "units writer after visual owner",
    )
    Writer.BeginObject(KUnitTable, 1)
    Writer.u16(len(KUnitClasses))
    WriteLengths(Writer, State)
    Display = State.Display
    Selectors = {
        **KExtraUnits,
        "moUnitSysUnits_c": Display.System,
        "moForceUnits_c": Display.Force,
        "moEnergyUnits_c": Display.Energy,
    }
    for Name in KUnitClasses[1:]:
        Writer.BeginObject(Name, 1)
        WriteUnitFields(Writer, "common")
        if Name == KDensityClass:
            WriteDensity(Writer, Display)
        elif Name in Selectors:
            Writer.u16(Selectors[Name])
