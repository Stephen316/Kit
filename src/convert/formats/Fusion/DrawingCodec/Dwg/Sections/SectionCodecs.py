from collections.abc import Mapping
from struct import error as StructError

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.AcDsCodec import (
    EmitAcDs,
    ReadAcDs,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.ByteCodec import (
    EmitByteSpec,
    ReadByteSpec,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.ByteSpecs import KByteSpecs
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.PreviewCodec import (
    EmitPreview,
    ReadPreview,
)

KPreviewName = "AcDb:Preview"
KAcDsName = "AcDb:AcDsPrototype_1b"


def IsTypedName(SectionName: str) -> bool:
    return SectionName in KByteSpecs or SectionName in (KPreviewName, KAcDsName)


def ReadSection(SectionName: str, DataValue: bytes, VersionText: str) -> DwgRecord:
    if SectionName == KPreviewName:
        return ReadPreview(DataValue)
    if SectionName == KAcDsName:
        return ReadAcDs(DataValue, VersionText)
    SpecText = KByteSpecs.get(SectionName)
    if SpecText is None:
        raise ValueError(f"DWG section {SectionName!r} has no typed codec")
    return ReadByteSpec(SpecText, DataValue, VersionText)


def EmitSection(SectionName: str, Record: DwgRecord, VersionText: str) -> bytes:
    if SectionName == KPreviewName:
        return EmitPreview(Record)
    if SectionName == KAcDsName:
        return EmitAcDs(Record, VersionText)
    SpecText = KByteSpecs.get(SectionName)
    if SpecText is None:
        raise ValueError(f"DWG section {SectionName!r} has no typed codec")
    return EmitByteSpec(SpecText, Record, VersionText)


def ReadSectionVars(
    Named: Mapping[str, bytes], VersionText: str
) -> tuple[tuple[str, DwgRecord], ...]:
    Found: list[tuple[str, DwgRecord]] = []
    for SectionName, DataValue in Named.items():
        if not IsTypedName(SectionName):
            continue
        try:
            Record = ReadSection(SectionName, DataValue, VersionText)
            IsExact = EmitSection(SectionName, Record, VersionText) == DataValue
        except (ValueError, StructError):
            continue
        if IsExact:
            Found.append((SectionName, Record))
    return tuple(Found)
