from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, AsmTable


def CheckTopology(
    Expected: tuple[AsmRecord, ...], Actual: AsmTable, Mapping: dict[int, int]
) -> None:
    for ExpectedId, Wanted in enumerate(Expected):
        Stored = Actual.Records[Mapping[ExpectedId]]
        if Wanted.Name != Stored.Name or len(Wanted.Tokens) != len(Stored.Tokens):
            raise ValueError("Unsupported Fusion BRep record payload")
        for Index, (LeftToken, RightToken) in enumerate(
            zip(Wanted.Tokens, Stored.Tokens, strict=True)
        ):
            if LeftToken[0] == 12:
                Reference = ReadAsmPtr(Wanted, Index)
                ExpectedRef = -1 if Reference == -1 else Mapping[Reference]
                if ReadAsmPtr(Stored, Index) != ExpectedRef:
                    raise ValueError("Fusion BRep record reference disagrees")
            elif LeftToken != RightToken:
                raise ValueError("Unsupported Fusion BRep semantic field")
