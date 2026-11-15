from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassRow import DwgClassRow


# drawing class table needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgClassTable:
    MaxClassNumber: int
    LeadCodes: tuple[int, ...]
    ClassRows: tuple[DwgClassRow, ...]
    CrcValue: int
