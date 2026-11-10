# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from struct import pack as PackData

from convert.formats.Fusion.MetaCursor import MetaCursor
from interchange.enums.EnumFeatures import FeatureKind

# class identity qualifies display fields before looking for their native labels
KFeatureFields = {
    "DD405BC2-D673-44F0-8833-5CB2A1C186C7": ("Extrude", FeatureKind.KExtrusion),
    "E3849A15-2FC6-42A0-AF3A-2F1D7273B406": ("Revolve", FeatureKind.KRevolution),
    "D869265F-F339-4751-A066-91D30F81FF08": ("WorkPlane", FeatureKind.KReference),
}


# typed labels share their native ordinal with reciprocal geometry records
def ReadLabelData(BodyValue: bytes, LabelText: str) -> tuple[str, int] | None:
    Marker = PackData("<I", len(LabelText)) + LabelText.encode("utf-16le")
    Start = BodyValue.find(Marker)
    if Start < 0 or BodyValue.find(Marker, Start + len(Marker)) >= 0:
        return None
    Cursor = MetaCursor(BodyValue)
    Cursor.Offset = Start + len(Marker)
    try:
        StoredIndex = Cursor.ReadLong()
        if StoredIndex < 2**32:
            return Cursor.ReadText(True, Maximum=1024), StoredIndex
    except ValueError:
        return None
    return None


# named records retain their source labels without assigning names to unknown classes
def ReadFeatLabel(BodyValue: bytes, ClassGuid: str) -> tuple[str, FeatureKind]:
    Fields = KFeatureFields.get(ClassGuid)
    if Fields is None:
        return "", FeatureKind.KNative
    LabelText, FeatureType = Fields
    LabelData = ReadLabelData(BodyValue, LabelText)
    return LabelData[0] if LabelData is not None else "", FeatureType
