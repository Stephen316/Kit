from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HardOwner,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import DraftRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import PlaceMut
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceNetwork import (
    EnlistMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KPaperNetwork,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.SlotFields import ReactorSlot
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.LinkReactors import (
    ChainFields,
)


def OwnedEntry(KeyText: str) -> DraftRecord:
    return DraftRecord((("IsOwned", 1), ("Dependency", HardOwner(KeyText))))


def PlaceActionMut(
    Ledger: DraftBook,
    ActionKey: str,
    BodyKey: str,
    Dependencies: tuple[str, ...],
    Params: tuple[str, ...],
) -> str:
    Index = EnlistMut(Ledger, ActionKey)
    _ = PlaceMut(
        Ledger,
        ActionKey,
        "ACDBASSOCACTION",
        {"Owner": SoftPointer(KPaperNetwork), **ReactorSlot(Ledger, ActionKey)},
        {
            "OwningNetwork": SoftPointer(KPaperNetwork),
            "ActionBody": HardOwner(BodyKey),
            "ActionIndex": Index,
            "MaxDependencyIndex": len(Dependencies),
            "DependencyCount": len(Dependencies),
            "Dependencies": tuple(OwnedEntry(KeyText) for KeyText in Dependencies),
            "OwnedParamCount": len(Params),
            "OwnedParams": tuple(HardOwner(KeyText) for KeyText in Params),
            "ValueParamCount": 0,
            "ValueParams": (),
        },
    )
    return ActionKey


def PlaceDependMut(
    Ledger: DraftBook,
    KeyText: str,
    ActionKey: str,
    Index: int,
    Target: str,
    IsWrite: int,
) -> str:
    return PlaceMut(
        Ledger,
        KeyText,
        "ACDBASSOCDEPENDENCY",
        {"Owner": SoftPointer(ActionKey)},
        {
            "IsWriteDependency": IsWrite,
            "EvalOrder": 0,
            "DependencyIndex": Index,
            "DependentOn": SoftPointer(Target),
            **ChainFields(Ledger, KeyText),
        },
    )


def PlaceParamMut(
    Ledger: DraftBook, KeyText: str, ClassName: str, ActionKey: str, Dependency: str
) -> str:
    ClassData = {"Dependency": SoftPointer(Dependency)} if Dependency else {}
    return PlaceMut(
        Ledger, KeyText, ClassName, {"Owner": SoftPointer(ActionKey)}, ClassData
    )
