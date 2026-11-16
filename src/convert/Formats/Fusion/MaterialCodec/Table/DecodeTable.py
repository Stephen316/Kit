from convert.Formats.Fusion.MaterialCodec.Limits import KMaxCount
from convert.Formats.Fusion.MaterialCodec.Table.AssetEntry import AssetEntry
from convert.Formats.Fusion.MaterialCodec.Wire.MaterialReader import MaterialReader


# the table operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
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
