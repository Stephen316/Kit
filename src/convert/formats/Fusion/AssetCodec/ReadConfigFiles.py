# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from uuid import UUID as ParseUuid

from convert.formats.Fusion.AssetCodec.ConfigLayout import KConfigClasses, KConfigPrefix
from convert.formats.Fusion.AssetCodec.SegmentFrame import SegmentFrame
from convert.formats.Fusion.MetaCursor import MetaCursor


# only an explicitly empty configuration may create sidecars from typed design references
def ReadConfigFiles(Design: SegmentFrame, EmptyConfig: bool) -> tuple[str, ...]:
    Spans = tuple(Value for Value in Design.Spans if Value.ClassGuid in KConfigClasses)
    if not Spans and EmptyConfig is False:
        return ()
    if (
        EmptyConfig is not True
        or len(Spans) != len(KConfigClasses)
        or any(not Value.IsPrimary for Value in Spans)
        or {Value.ClassGuid for Value in Spans} != KConfigClasses.keys()
    ):
        raise ValueError("Fusion asset requires an explicitly empty configuration pair")
    Entries: dict[str, str] = {}
    Identities: set[str] = set()
    for SpanValue in Spans:
        Prefix, Extension = KConfigClasses[SpanValue.ClassGuid]
        if (
            SpanValue.ClassSpace != "Fusion"
            or SpanValue.EndOffset - SpanValue.PayloadOffset > 256
        ):
            raise ValueError("Invalid Fusion asset configuration trigger")
        Cursor = MetaCursor(
            Design.BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset]
        )
        if Cursor.ReadText(
            Maximum=64
        ) != Prefix + "SerializerTrigger" or Cursor.TakeBytes(2) != bytes(2):
            raise ValueError("Invalid Fusion asset configuration trigger")
        NameValue = Cursor.ReadText(True, Maximum=128)
        Label = NameValue.removeprefix(Prefix + ".").removesuffix(Extension)
        try:
            Canonical = str(ParseUuid(Label))
        except ValueError as ErrorInfo:
            raise ValueError(
                "Invalid Fusion asset configuration member name"
            ) from ErrorInfo
        if (
            Cursor.Offset != len(Cursor.DataValue)
            or NameValue != Prefix + "." + Label + Extension
            or Canonical != Label
            or Label in Identities
        ):
            raise ValueError("Invalid Fusion asset configuration member name")
        Identities.add(Label)
        Entries[SpanValue.ClassGuid] = KConfigPrefix + NameValue
    return tuple(Entries[ClassGuid] for ClassGuid in KConfigClasses)
