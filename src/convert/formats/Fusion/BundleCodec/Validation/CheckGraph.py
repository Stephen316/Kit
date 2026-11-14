from convert.formats.Fusion.BundleCodec.Model.BundleGraph import BundleGraph


def CheckGraph(Value: BundleGraph) -> None:
    Neighbors = {
        Entry.ObjectId: {
            Target for Group in Entry.References for Target in Group.Targets
        }
        for Entry in Value.Objects
    }
    Incoming = dict.fromkeys(Neighbors, 0)
    for Targets in Neighbors.values():
        for Target in Targets:
            Incoming[Target] += 1
    Pending = [Value.RootIds[0]] if Incoming[Value.RootIds[0]] == 0 else []
    Visited: set[int] = set()
    while Pending:
        ObjectId = Pending.pop()
        Visited.add(ObjectId)
        for Child in Neighbors[ObjectId]:
            Incoming[Child] -= 1
            if Incoming[Child] == 0:
                Pending.append(Child)
    if Visited != set(Neighbors):
        raise ValueError("Cyclic or unreachable Fusion bundle document")
