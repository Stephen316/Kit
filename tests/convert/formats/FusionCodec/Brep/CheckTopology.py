from convert.formats.Fusion.Topology.AsmEdge.AsmFields import IsAsmFlag
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def CheckTopology(Table: AsmTable) -> None:
    for Identity, Record in enumerate(Table.Records):
        for Index, Token in enumerate(Record.Tokens):
            if Token[0] == 12:
                assert -1 <= ReadAsmPtr(Record, Index) < len(Table.Records)
        if Record.Name != "coedge":
            continue
        NextUse = RequireAsm(Table, ReadAsmPtr(Record, 3), "coedge", 11)
        PriorUse = RequireAsm(Table, ReadAsmPtr(Record, 4), "coedge", 11)
        assert ReadAsmPtr(NextUse, 4) == Identity
        assert ReadAsmPtr(PriorUse, 3) == Identity
        PartnerId = ReadAsmPtr(Record, 5)
        if PartnerId == -1:
            continue
        Partner = RequireAsm(Table, PartnerId, "coedge", 11)
        assert ReadAsmPtr(Partner, 5) == Identity
        assert ReadAsmPtr(Partner, 6) == ReadAsmPtr(Record, 6)
        assert IsAsmFlag(Partner, 7) != IsAsmFlag(Record, 7)
