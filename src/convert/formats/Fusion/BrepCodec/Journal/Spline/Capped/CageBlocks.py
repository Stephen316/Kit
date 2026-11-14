from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
)


def GroupBlocks(
    Graph: CageGraph, Drawn: tuple[bool, ...]
) -> tuple[tuple[int, ...], ...]:
    Owner = [-1] * len(Graph.Loops)
    Blocks: list[tuple[int, ...]] = []
    for FirstFace in range(len(Graph.Loops)):
        if Owner[FirstFace] >= 0:
            continue
        Owner[FirstFace] = len(Blocks)
        Queue = [FirstFace]
        for FaceIndex in Queue:
            for LinkIndex in Graph.Loops[FaceIndex]:
                Across = Graph.Links[Graph.Links[LinkIndex].Opposite].FaceIndex
                if not Drawn[LinkIndex] and Across >= 0 and Owner[Across] < 0:
                    Owner[Across] = len(Blocks)
                    Queue.append(Across)
        Blocks.append(tuple(sorted(Queue)))
    return tuple(Blocks)
