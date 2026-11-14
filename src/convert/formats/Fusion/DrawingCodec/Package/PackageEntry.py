from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout


@MakeDataClass(frozen=True, slots=True)
class PackageEntry:
    Name: str
    Payload: bytes
    Layout: EntryLayout
