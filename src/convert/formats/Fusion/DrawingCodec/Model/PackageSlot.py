from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout


# package slot needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class PackageSlot:
    Name: str
    Layout: EntryLayout
