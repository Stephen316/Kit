from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout


@MakeDataClass(frozen=True, slots=True)
class PackageSlot:
    Name: str
    Layout: EntryLayout
