from convert.formats.Fusion.Assembly.AssemblyIndex import AssemblyIndex
from convert.formats.Fusion.Assembly.NativeOccurrence import NativeOccur


# exact collection ownership supplies child order without expanding reused definitions
def LinkOccurrences(IndexValue: AssemblyIndex) -> tuple[NativeOccur, ...]:
    Linked: list[NativeOccur] = []
    Claimed: set[int] = set()
    ByOwner: set[int] = set()
    for CollectionId, (OwnerId, Members) in IndexValue.Collections.items():
        Owner = IndexValue.Components.get(OwnerId)
        if Owner is None or Owner.CollectionId != CollectionId or OwnerId in ByOwner:
            raise ValueError(
                "Fusion component and occurrence collection links disagree"
            )
        ByOwner.add(OwnerId)
        Siblings: set[tuple[int, int]] = set()
        for Order, MemberId in enumerate(Members):
            Occurrence = IndexValue.Occurrences.get(MemberId)
            if (
                Occurrence is None
                or Occurrence.CollectionId != CollectionId
                or MemberId in Claimed
            ):
                raise ValueError(
                    "Fusion occurrence and parent collection links disagree"
                )
            Component = IndexValue.Components.get(Occurrence.ComponentId)
            if Component is None:
                raise ValueError("Fusion occurrence has no local component")
            InstanceKey = (Occurrence.ComponentId, Occurrence.InstanceNumber)
            if InstanceKey in Siblings:
                raise ValueError("Duplicate Fusion sibling instance number")
            Siblings.add(InstanceKey)
            Claimed.add(MemberId)
            NameValue = Occurrence.Name
            if not NameValue and Component.Component.Name:
                NameValue = f"{Component.Component.Name}:{Occurrence.InstanceNumber}"
            Linked.append(
                NativeOccur(
                    MemberId,
                    Occurrence.ComponentId,
                    OwnerId,
                    NameValue,
                    Occurrence.InstanceNumber,
                    Occurrence.NativeGuid,
                    Order,
                    Occurrence.Transform,
                )
            )
    CheckAsmOwners(IndexValue, ByOwner, Claimed)
    return tuple(Linked)


# reciprocal collection coverage catches missing parents and unclaimed occurrences
def CheckAsmOwners(
    IndexValue: AssemblyIndex, ByOwner: set[int], Claimed: set[int]
) -> None:
    if ByOwner != IndexValue.Components.keys():
        raise ValueError("Missing Fusion component occurrence collection")
    if Claimed != {
        Record.ObjectId
        for Record in IndexValue.Occurrences.values()
        if Record.CollectionId is not None
    }:
        raise ValueError("Fusion occurrence is absent from its declared collection")
