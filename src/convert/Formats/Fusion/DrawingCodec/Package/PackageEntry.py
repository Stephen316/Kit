from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout


# package entry needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class PackageEntry:
    Name: str
    Payload: bytes
    Layout: EntryLayout
