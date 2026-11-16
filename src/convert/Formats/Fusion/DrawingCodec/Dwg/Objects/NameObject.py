from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgClassTable import DwgClassTable
from convert.Formats.Fusion.DrawingCodec.Dwg.Objects.FixedTypes import (
    KEntityTypes,
    KFixedTypes,
)

# entity class id must remain consistent across callers so section boundaries and object references remain consistent
KEntityClassId = 0x1F2


# name object needs an explicit validity boundary so section boundaries and object references remain consistent
def NameObject(TypeNumber: int, ClassTable: DwgClassTable) -> tuple[str, bool]:
    if TypeNumber < 500:
        return KFixedTypes.get(TypeNumber, ""), TypeNumber in KEntityTypes
    for ClassRow in ClassTable.ClassRows:
        if ClassRow.ClassNumber == TypeNumber:
            return ClassRow.DxfName, ClassRow.ItemClassId == KEntityClassId
    raise ValueError(f"DWG object type {TypeNumber} has no class definition")
