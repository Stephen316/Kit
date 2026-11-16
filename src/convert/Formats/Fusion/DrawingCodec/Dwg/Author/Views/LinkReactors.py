from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import SoftPointer
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftRow
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftLink,
    DraftSlot,
    KDraftValue,
    KSlotFirst,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import AppendMut
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.SlotFields import DeclareMut

# the dependency kinds order must stay explicit so projected geometry retains its paper and model relationships
KDependencyKinds = ("ACDBASSOCDEPENDENCY", "ACDBASSOCGEOMDEPENDENCY")


# the chain fields contract needs a shared interpretation so projected geometry retains its paper and model relationships
def ChainFields(Ledger: DraftBook, KeyText: str) -> dict[str, KDraftValue]:
    return {
        "PrevDependency": DraftSlot(DeclareMut(Ledger, KeyText + ".Prev"), KSlotFirst),
        "NextDependency": DraftSlot(DeclareMut(Ledger, KeyText + ".Next"), KSlotFirst),
    }


# link key must resolve unambiguously so projected geometry retains its paper and model relationships
def LinkKey(Value: KDraftValue) -> str:
    if not isinstance(Value, DraftLink):
        raise ValueError("Authored DWG dependency names no placed object")
    return Value.KeyText


# the watched contract needs a shared interpretation so projected geometry retains its paper and model relationships
def Watched(Entry: DraftRow) -> tuple[str, tuple[str, ...]]:
    Fields = dict(Entry.ClassData.DraftFields)
    Target = LinkKey(Fields["DependentOn"])
    Chain = Fields.get("PathObjects", ())
    Others = (
        tuple(LinkKey(Member) for Member in Chain) if isinstance(Chain, tuple) else ()
    )
    return Target, Others


# react needs an explicit validity boundary so projected geometry retains its paper and model relationships
def ReactMut(Ledger: DraftBook, Target: str, KeyText: str) -> None:
    SlotName = Target + ".Reactors"
    if SlotName not in Ledger.SlotItems:
        raise ValueError(f"Authored DWG object {Target!r} takes no reactors")
    Pointer = SoftPointer(KeyText)
    if Pointer not in Ledger.SlotItems[SlotName]:
        AppendMut(Ledger, SlotName, Pointer)


# link reactors must resolve unambiguously so projected geometry retains its paper and model relationships
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
