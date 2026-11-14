from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismLine import PrismLine
from convert.formats.Fusion.BrepCodec.Prism.Writing.FreshPrism import FreshPrism
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody


def CuboidFrame(Model: CuboidBody) -> PrismFrame:
    Frame = FreshPrism(Model)
    Boundary = ((0, 1), (1, 3), (3, 2), (2, 0))
    Edges = list(Frame.Edges)
    for Index, EdgeValue in enumerate(Edges):
        if (EdgeValue.EndCorner, EdgeValue.StartCorner) not in Boundary:
            continue
        Origin = Frame.CornersCm[EdgeValue.EndCorner]
        Finish = Frame.CornersCm[EdgeValue.StartCorner]
        Direction = (
            Finish[0] - Origin[0],
            Finish[1] - Origin[1],
            Finish[2] - Origin[2],
        )
        Edges[Index] = ReplaceValue(
            EdgeValue,
            StartCorner=EdgeValue.EndCorner,
            EndCorner=EdgeValue.StartCorner,
            Curve=PrismLine(Origin, Direction),
        )
    return ReplaceValue(Frame, Edges=tuple(Edges))
