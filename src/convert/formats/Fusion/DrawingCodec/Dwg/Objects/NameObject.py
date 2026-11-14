from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassTable import DwgClassTable
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.FixedTypes import (
    KEntityTypes,
    KFixedTypes,
)

KEntityClassId = 0x1F2


def NameObject(TypeNumber: int, ClassTable: DwgClassTable) -> tuple[str, bool]:
    if TypeNumber < 500:
        return KFixedTypes.get(TypeNumber, ""), TypeNumber in KEntityTypes
    for ClassRow in ClassTable.ClassRows:
        if ClassRow.ClassNumber == TypeNumber:
            return ClassRow.DxfName, ClassRow.ItemClassId == KEntityClassId
    raise ValueError(f"DWG object type {TypeNumber} has no class definition")
