from convert.formats.Fusion.MaterialCodec.Limits import KMaxCount
from convert.formats.Fusion.MaterialCodec.Table.AssetEntry import AssetEntry
from convert.formats.Fusion.MaterialCodec.Wire.MaterialReader import MaterialReader


def DecodeTable(Payload: bytes) -> tuple[AssetEntry, ...]:
    Reader = MaterialReader(Payload)
    Entries: list[AssetEntry] = []
    while Reader.Offset < len(Payload):
        if len(Entries) >= KMaxCount:
            raise ValueError("Fusion material table exceeds the count limit")
        Entries.append(
            AssetEntry(
                Reader.ReadText(),
                Reader.ReadText(),
                Reader.ReadUInt(),
                Reader.ReadUInt(),
                Reader.ReadText(),
            )
        )
    Reader.RequireEnd()
    return tuple(Entries)
