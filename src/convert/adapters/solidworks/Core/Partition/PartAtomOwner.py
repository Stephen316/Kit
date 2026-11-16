from struct import Struct
from typing import cast as CastValue

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.Partition.PartRecordBody import FindPartBodies

# scope ownership uses a named parasolid attribute with its checked definition domain
KAtomName = b"ATOM_ID_2001"

# the attribute name length frames its complete encoded identifier
KNameRecord = Struct(">IH12s")

# the definition binds the attribute name before its counted references
KDefRecord = Struct(">IHHHi24x")

# each attribute carries its owner and value reference in the native layout
KOwnerRecord = Struct(">IHI8H")

# a separate integer record supplies the atom value for its referring attribute
KValueRecord = Struct(">IHi")


# the name and definition must resolve uniquely before reading body attributes
def ReadAtomDef(DataValue: bytes) -> int:
    Names = [
        Index
        for Start in FindPartBodies(DataValue, 79, KNameRecord.size)
        for Length, Index, NameValue in (KNameRecord.unpack_from(DataValue, Start),)
        if (Length, NameValue) == (len(KAtomName), KAtomName) and Index > 1
    ]
    RequireArch(len(Names), 1, "unique partition atom name")
    Definitions = [
        Index
        for Start in FindPartBodies(DataValue, 80, KDefRecord.size)
        for Count, Index, _, NameIndex, Domain in (
            KDefRecord.unpack_from(DataValue, Start),
        )
        if (Count, NameIndex, Domain) == (2, Names[0], 9000) and Index > 1
    ]
    RequireArch(len(Definitions), 1, "unique partition atom definition")
    return CastValue(int, Definitions[0])


# each shell owner needs one distinct attribute record and integer reference
def ReadOwnerRefs(DataValue: bytes, Owners: frozenset[int]) -> dict[int, int]:
    Definition = ReadAtomDef(DataValue)
    OwnerRows = [
        (Owner, Attribute, RefValue)
        for Start in FindPartBodies(DataValue, 81, KOwnerRecord.size)
        for Count, Attribute, NodeId, DefIndex, Owner, _, _, _, _, NullValue, RefValue in (
            KOwnerRecord.unpack_from(DataValue, Start),
        )
        if (Count, DefIndex, NullValue) == (2, Definition, 1)
        and NodeId > 0
        and min(Attribute, Owner, RefValue) > 1
    ]
    RequireArch(
        {Owner for Owner, _, _ in OwnerRows},
        Owners,
        "atom attributes cover exactly the shell owners",
    )
    RequireArch(
        (
            len(OwnerRows),
            len({Attribute for _, Attribute, _ in OwnerRows}),
            len({RefValue for _, _, RefValue in OwnerRows}),
        ),
        (len(Owners),) * 3,
        "unique atom attributes and values for the shell owners",
    )
    return {Owner: RefValue for Owner, _, RefValue in OwnerRows}


# duplicate integer records cannot silently replace a body identity
def ReadOwnerAtoms(DataValue: bytes, Owners: frozenset[int]) -> dict[int, int]:
    OwnerRefs = ReadOwnerRefs(DataValue, Owners)
    Expected = set(OwnerRefs.values())
    Values: dict[int, int] = {}
    for Start in FindPartBodies(DataValue, 82, KValueRecord.size):
        Count, Index, AtomId = KValueRecord.unpack_from(DataValue, Start)
        if Count == 1 and Index in Expected:
            RequireArch(
                Index not in Values and AtomId > 0, True, "unique positive atom ID"
            )
            Values[Index] = AtomId
    RequireArch(set(Values), Expected, "atom integer references resolve")
    RequireArch(
        len(set(Values.values())), len(Owners), "distinct atoms for the shell owners"
    )
    return {Owner: Values[Reference] for Owner, Reference in OwnerRefs.items()}
