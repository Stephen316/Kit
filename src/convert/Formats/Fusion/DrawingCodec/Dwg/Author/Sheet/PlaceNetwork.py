from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HardOwner,
    KNullSoft,
    SoftPointer,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftRecord,
    DraftSlot,
    KSlotCount,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    AppendMut,
    PlaceMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceFolder import (
    EnrolMut,
    PlaceFolderMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KNamedObjects,
    KNetworkActions,
    KPaperFolder,
    KPaperNetwork,
    KPaperNetworks,
    KPaperSpace,
    KRootNetwork,
    KRootNetworks,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.SlotFields import CountedSlot

# network name must remain consistent across callers so paper layouts retain consistent object ownership
KNetworkName = "ACAD_ASSOCNETWORK"


# the action entry contract needs a shared interpretation so paper layouts retain consistent object ownership
def ActionEntry(IsOwned: int, ActionKey: str) -> DraftRecord:
    Action = HardOwner(ActionKey) if IsOwned else SoftPointer(ActionKey)
    return DraftRecord((("IsOwned", IsOwned), ("Action", Action)))


# the network operation needs a consistent construction rule so paper layouts retain consistent object ownership
def PlaceNetworkMut(Ledger: DraftBook) -> None:
    _ = PlaceFolderMut(Ledger, KPaperFolder, KPaperSpace, True, KNetworkName)
    _ = PlaceFolderMut(Ledger, KPaperNetworks, KPaperFolder, False, KNetworkName)
    _ = PlaceMut(
        Ledger,
        KPaperNetwork,
        "ACDBASSOCNETWORK",
        {
            "Owner": SoftPointer(KPaperNetworks),
            "Reactors": (SoftPointer(KPaperNetworks),),
        },
        {
            "OwningNetwork": SoftPointer(KRootNetwork),
            "ActionIndex": 1,
            "MaxActionIndex": DraftSlot(KNetworkActions, KSlotCount),
            **CountedSlot(Ledger, KNetworkActions, "ActionCount", "Actions"),
        },
    )
    _ = PlaceFolderMut(Ledger, KRootNetworks, KNamedObjects, False, KNetworkName)
    _ = EnrolMut(Ledger, KNamedObjects, KNetworkName, KRootNetworks)
    _ = PlaceMut(
        Ledger,
        KRootNetwork,
        "ACDBASSOCNETWORK",
        {
            "Owner": SoftPointer(KRootNetworks),
            "Reactors": (SoftPointer(KRootNetworks),),
        },
        {
            "OwningNetwork": KNullSoft,
            "ActionIndex": 0,
            "MaxActionIndex": 1,
            "ActionCount": 1,
            "Actions": (ActionEntry(0, KPaperNetwork),),
        },
    )


# the enlist contract needs a shared interpretation so paper layouts retain consistent object ownership
def EnlistMut(Ledger: DraftBook, ActionKey: str) -> int:
    AppendMut(Ledger, KNetworkActions, ActionEntry(1, ActionKey))
    return len(Ledger.SlotItems[KNetworkActions])
