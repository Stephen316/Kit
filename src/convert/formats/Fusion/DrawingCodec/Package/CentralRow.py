from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout


# central row needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class CentralRow:
    Name: str
    NameBytes: bytes
    Layout: EntryLayout
    Checksum: int
    Packed: int
    Size: int
    Offset: int
