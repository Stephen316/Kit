from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout


@MakeDataClass(frozen=True, slots=True)
class CentralRow:
    Name: str
    NameBytes: bytes
    Layout: EntryLayout
    Checksum: int
    Packed: int
    Size: int
    Offset: int
