# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import cast as CastValue
from uuid import UUID as ParseUuid

from convert.formats.Fusion.SegmentCodec.Metadata.MetaLimits import KMaxMetaText
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink


# manifests share metadata packing but permit bounded description line breaks
class ManifestSink(MetaSink):
    __slots__ = ()

    # canonical tokens match the document reader and preserve exact token spelling
    def AddGuid(self, GuidText: str) -> None:
        if type(GuidText) is not str or len(GuidText) != 36:
            raise ValueError("Invalid Fusion manifest GUID")
        GuidValue = ParseUuid(GuidText)
        if GuidValue.int == 0 or str(GuidValue) != GuidText:
            raise ValueError("Invalid Fusion manifest GUID")
        self.AddText(GuidText, WideText=True)

    # manifest descriptions allow native line breaks but still count encoded units
    def AddDescription(self, Content: str) -> None:
        if (
            type(Content) is not str
            or len(Content) > KMaxMetaText
            or not all(Letter.isprintable() or Letter in "\r\n\t" for Letter in Content)
        ):
            raise ValueError("Invalid Fusion manifest description")
        DataValue = Content.encode("utf-16le")
        Count = len(DataValue) // 2
        if Count > KMaxMetaText:
            raise ValueError("Oversized Fusion manifest description")
        self.AddWord(Count)
        self.AddBytes(DataValue)

    # the required key order ties every typed version value to its correct wire field
    def AddVersions(
        self, Values: tuple[tuple[str, int], ...], KeysValue: tuple[str, ...]
    ) -> None:
        self.AddCount(Values, len(KeysValue))
        if len(Values) != len(KeysValue):
            raise ValueError("Invalid Fusion manifest version count")
        for Entry, KeyName in zip(Values, KeysValue, strict=True):
            if (
                type(Entry) is not tuple
                or len(CastValue(tuple[object, ...], Entry)) != 2
                or type(Entry[0]) is not str
                or Entry[0] != KeyName
            ):
                raise ValueError("Invalid Fusion manifest version keys")
            self.AddText(KeyName)
            self.AddWord(Entry[1])
