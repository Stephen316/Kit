from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassRow import DwgClassRow


@MakeDataClass(frozen=True, slots=True)
class DwgClassTable:
    MaxClassNumber: int
    LeadCodes: tuple[int, ...]
    ClassRows: tuple[DwgClassRow, ...]
    CrcValue: int
