from collections import deque as MakeQueue

from convert.formats.Fusion.BrepCodec.Reading.ReadLinkPairs import ReadLinkPairs
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, AsmTable


def MapTopology(Expected: tuple[AsmRecord, ...], Actual: AsmTable) -> dict[int, int]:
    if len(Expected) != len(Actual.Records):
        raise ValueError("Unsupported Fusion BRep entity count")
    Mapping = {Index: Index for Index in range(Actual.RootCount)}
    Reverse = dict(Mapping)
    Pending = MakeQueue(Mapping.items())
    while Pending:
        ExpectedId, ActualId = Pending.popleft()
        Wanted, Stored = Expected[ExpectedId], Actual.Records[ActualId]
        for ExpectedRef, ActualRef in ReadLinkPairs(
            Wanted, Stored, len(Actual.Records)
        ):
            if ExpectedRef in Mapping:
                if Mapping[ExpectedRef] != ActualRef:
                    raise ValueError("Fusion BRep topology link disagrees")
            else:
                if ActualRef in Reverse:
                    raise ValueError("Fusion BRep topology aliases distinct entities")
                Mapping[ExpectedRef] = ActualRef
                Reverse[ActualRef] = ExpectedRef
                Pending.append((ExpectedRef, ActualRef))
    if len(Mapping) != len(Expected):
        raise ValueError("Unreachable Fusion BRep entity")
    return Mapping
