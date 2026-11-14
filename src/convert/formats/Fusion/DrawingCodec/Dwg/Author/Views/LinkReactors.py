from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import SoftPointer
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftRow
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftLink,
    DraftSlot,
    KDraftValue,
    KSlotFirst,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import AppendMut
from convert.formats.Fusion.DrawingCodec.Dwg.Author.SlotFields import DeclareMut

KDependencyKinds = ("ACDBASSOCDEPENDENCY", "ACDBASSOCGEOMDEPENDENCY")


def ChainFields(Ledger: DraftBook, KeyText: str) -> dict[str, KDraftValue]:
    return {
        "PrevDependency": DraftSlot(DeclareMut(Ledger, KeyText + ".Prev"), KSlotFirst),
        "NextDependency": DraftSlot(DeclareMut(Ledger, KeyText + ".Next"), KSlotFirst),
    }


def LinkKey(Value: KDraftValue) -> str:
    if not isinstance(Value, DraftLink):
        raise ValueError("Authored DWG dependency names no placed object")
    return Value.KeyText


def Watched(Entry: DraftRow) -> tuple[str, tuple[str, ...]]:
    Fields = dict(Entry.ClassData.DraftFields)
    Target = LinkKey(Fields["DependentOn"])
    Chain = Fields.get("PathObjects", ())
    Others = (
        tuple(LinkKey(Member) for Member in Chain) if isinstance(Chain, tuple) else ()
    )
    return Target, Others


def ReactMut(Ledger: DraftBook, Target: str, KeyText: str) -> None:
    SlotName = Target + ".Reactors"
    if SlotName not in Ledger.SlotItems:
        raise ValueError(f"Authored DWG object {Target!r} takes no reactors")
    Pointer = SoftPointer(KeyText)
    if Pointer not in Ledger.SlotItems[SlotName]:
        AppendMut(Ledger, SlotName, Pointer)


def LinkReactorsMut(Ledger: DraftBook) -> None:
    Chains: dict[str, list[str]] = {}
    for Entry in Ledger.DraftRows:
        if Entry.ClassName not in KDependencyKinds:
            continue
        Target, Others = Watched(Entry)
        for Watcher in (Target, *Others):
            ReactMut(Ledger, Watcher, Entry.KeyText)
        Chains.setdefault(Target, []).append(Entry.KeyText)
    for Chain in Chains.values():
        for Earlier, Later in zip(Chain, Chain[1:]):
            AppendMut(Ledger, Earlier + ".Next", SoftPointer(Later))
            AppendMut(Ledger, Later + ".Prev", SoftPointer(Earlier))
