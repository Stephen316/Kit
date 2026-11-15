from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.EntityCodec.Schema.NamedType import NamedType
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType


# shared named profile setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def NamedProfile(Profile: EntityProfile, TargetGuid: str = "") -> EntityProfile:
    return ReplaceValue(
        Profile,
        NamedTypes=(
            NamedType("StrongRefMetaType", WireType("ref", ClassGuid=TargetGuid)),
            NamedType("IntrinsicMetaTypeHString", WireType("ascii")),
        ),
    )
