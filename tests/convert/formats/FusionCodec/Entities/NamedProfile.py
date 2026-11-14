from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.EntityCodec.Schema.NamedType import NamedType
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType


def NamedProfile(Profile: EntityProfile, TargetGuid: str = "") -> EntityProfile:
    return ReplaceValue(
        Profile,
        NamedTypes=(
            NamedType("StrongRefMetaType", WireType("ref", ClassGuid=TargetGuid)),
            NamedType("IntrinsicMetaTypeHString", WireType("ascii")),
        ),
    )
