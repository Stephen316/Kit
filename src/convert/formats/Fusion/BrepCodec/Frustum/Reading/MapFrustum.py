from collections import deque as MakeQueue

from convert.formats.Fusion.BrepCodec.Frustum.Reading.FrustumLinks import FrustumLinks
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, AsmTable


def MapFrustum(Expected: tuple[AsmRecord, ...], Actual: AsmTable) -> dict[int, int]:
    if len(Expected) != len(Actual.Records):
        raise ValueError("Unsupported frustum entity count")
    Mapping = {Index: Index for Index in range(Actual.RootCount)}
    Reverse = dict(Mapping)
    Pending = MakeQueue(Mapping.items())
    while Pending:
        ExpectedId, ActualId = Pending.popleft()
        Wanted, Stored = Expected[ExpectedId], Actual.Records[ActualId]
        for ExpectedRef, ActualRef in FrustumLinks(Wanted, Stored, len(Actual.Records)):
            if ExpectedRef in Mapping:
                if Mapping[ExpectedRef] != ActualRef:
                    raise ValueError("Frustum topology link disagrees")
            else:
                if ActualRef in Reverse:
                    raise ValueError("Frustum topology aliases distinct entities")
                Mapping[ExpectedRef] = ActualRef
                Reverse[ActualRef] = ExpectedRef
                Pending.append((ExpectedRef, ActualRef))
    if len(Mapping) != len(Expected):
        raise ValueError("Unreachable frustum entity")
    return Mapping
