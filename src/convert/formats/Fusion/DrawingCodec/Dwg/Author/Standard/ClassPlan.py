from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.ClassVocab import (
    KClassFamilies,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassRow import DwgClassRow

# first class must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KFirstClass = 500


# the plan classes contract needs a stable decomposition so native drawing objects use a consistent symbol vocabulary
def PlanClasses(Ledger: DraftBook) -> tuple[DwgClassRow, ...]:
    UsedKinds = {Entry.ClassName for Entry in Ledger.DraftRows}
    ClassRows: list[DwgClassRow] = []
    for Family, Members in KClassFamilies:
        AppName, ProxyFlags, ItemClass, Release, Maintenance = Family
        for DxfName, CppName in Members:
            if DxfName not in UsedKinds:
                continue
            ClassRows.append(
                DwgClassRow(
                    KFirstClass + len(ClassRows),
                    ProxyFlags,
                    AppName,
                    CppName,
                    DxfName,
                    False,
                    ItemClass,
                    0,
                    Release,
                    Maintenance,
                    0,
                    0,
                )
            )
    return tuple(ClassRows)
