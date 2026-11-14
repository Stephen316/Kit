from convert.formats.Fusion.SegmentCodec.Chronology.PackHistRefs import (
    IsHistId,
    KMaxHistRefs,
)
from convert.formats.Fusion.SegmentCodec.Parameters.ParamScope import ParamScope


def CheckParamScope(Value: ParamScope) -> None:
    Owners = (Value.CollectionId, Value.RegistryId, Value.ComponentId)
    if (
        any(not IsHistId(Identity) or Identity == 0 for Identity in Owners)
        or len(set(Owners)) != 3
        or type(Value.HighWaterMark) is not int
        or not 0 <= Value.HighWaterMark < 1 << 32
        or type(Value.MemberIds) is not tuple
        or len(Value.MemberIds) > KMaxHistRefs
        or any(
            not IsHistId(Identity) or Identity == 0 or Identity in Owners
            for Identity in Value.MemberIds
        )
        or len(set(Value.MemberIds)) != len(Value.MemberIds)
        or type(Value.NameRows) is not tuple
        or len(Value.NameRows) != len(Value.MemberIds)
    ):
        raise ValueError("Invalid Fusion parameter scope identities")
    Names: set[str] = set()
    Identities: set[int] = set()
    Members = frozenset(Value.MemberIds)
    for Entry in Value.NameRows:
        if type(Entry) is not tuple or len(Entry) != 2:
            raise ValueError("Invalid Fusion parameter name row")
        Identity, Content = Entry
        if (
            not IsHistId(Identity)
            or Identity not in Members
            or Identity in Identities
            or type(Content) is not str
            or not Content
            or Content in Names
        ):
            raise ValueError("Invalid Fusion parameter name mapping")
        Names.add(Content)
        Identities.add(Identity)
