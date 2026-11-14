from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HardOwner,
    KNullSoft,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftRecord,
    DraftSlot,
    KSlotCount,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    AppendMut,
    PlaceMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceFolder import (
    EnrolMut,
    PlaceFolderMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KNamedObjects,
    KNetworkActions,
    KPaperFolder,
    KPaperNetwork,
    KPaperNetworks,
    KPaperSpace,
    KRootNetwork,
    KRootNetworks,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.SlotFields import CountedSlot

KNetworkName = "ACAD_ASSOCNETWORK"


def ActionEntry(IsOwned: int, ActionKey: str) -> DraftRecord:
    Action = HardOwner(ActionKey) if IsOwned else SoftPointer(ActionKey)
    return DraftRecord((("IsOwned", IsOwned), ("Action", Action)))


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


def EnlistMut(Ledger: DraftBook, ActionKey: str) -> int:
    AppendMut(Ledger, KNetworkActions, ActionEntry(1, ActionKey))
    return len(Ledger.SlotItems[KNetworkActions])
