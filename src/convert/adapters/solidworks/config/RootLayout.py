from dataclasses import dataclass as DataClass, replace as ReplaceData
from importlib.resources import files as ResFiles
import json as JsonModule

from convert.adapters.solidworks.container.Archive import (
    ArchiveError,
    IsLayoutObject,
    LayoutTable,
)

# the root seed and inline fields have been independently checked for this generation
KConfigGen = 19000

# native configuration archives enter through the same registered part class
KRootClass = "moPart_c"


# staged layout scopes prevent early wildcard children from seeing later definitions
@DataClass(frozen=True, slots=True)
class PartLayouts:
    Prefix: LayoutTable
    Material: LayoutTable
    Atoms: LayoutTable


# the format grammar must remain available when the package is installed alone
def LoadPartLayouts() -> PartLayouts:
    Resource = ResFiles("convert.adapters.solidworks.config").joinpath(
        "RootLayout.json"
    )
    Value: object = JsonModule.loads(Resource.read_text(encoding="utf-8"))
    if not IsLayoutObject(Value):
        raise ArchiveError("invalid packaged configuration layout")
    return PartLayouts(
        LayoutTable.FromMapping({"classes": Value["prefix"]}),
        LayoutTable.FromMapping({"classes": Value["material"]}),
        LayoutTable.FromMapping({"classes": Value["atoms"]}),
    )


# each new root child gets its preceding scalar width from actual archive framing
def ExtendRoot(
    Layouts: LayoutTable,
    OtherLayouts: LayoutTable,
    Slots: tuple[str, ...],
    Widths: tuple[int, ...],
) -> LayoutTable:
    RootLayout = Layouts[KRootClass]
    Entries = {**Layouts.classes, **OtherLayouts.classes}
    StartSlot = len(RootLayout.child_slots) - 1
    RunWidths = {
        **RootLayout.runs,
        **{str(SlotIndex): Width for SlotIndex, Width in enumerate(Widths, StartSlot)},
    }
    Entries[KRootClass] = ReplaceData(
        RootLayout, child_slots=RootLayout.child_slots + Slots, runs=RunWidths
    )
    return ReplaceData(Layouts, classes=Entries)
