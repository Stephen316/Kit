from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology
from convert.formats.Fusion.TSplineCodec.Validation.CheckIndices import CheckIndices


def CheckLinks(Topology: CageTopology) -> None:
    for Index, LinkValue in enumerate(Topology.Links):
        CheckIndices(
            (LinkValue.Previous, LinkValue.NextLink, LinkValue.Opposite),
            len(Topology.Links),
            "link",
        )
        CheckIndices((LinkValue.VertexIndex,), len(Topology.Vertices), "vertex")
        CheckIndices((LinkValue.EdgeIndex,), len(Topology.Edges), "edge")
        if type(LinkValue.FaceIndex) is not int or not -1 <= LinkValue.FaceIndex < len(
            Topology.Faces
        ):
            raise ValueError("Invalid TSM face reference")
        if (
            type(LinkValue.ValenceOffset) is not int
            or not 0 <= LinkValue.ValenceOffset <= 3
        ):
            raise ValueError("Unsupported TSM link flags")
        Previous, Following, Opposite = (
            Topology.Links[Value]
            for Value in (LinkValue.Previous, LinkValue.NextLink, LinkValue.Opposite)
        )
        if (
            Previous.NextLink != Index
            or Following.Previous != Index
            or Opposite.Opposite != Index
            or LinkValue.Opposite == Index
        ):
            raise ValueError("Nonreciprocal TSM links")
        if (
            Previous.FaceIndex != LinkValue.FaceIndex
            or Following.FaceIndex != LinkValue.FaceIndex
        ):
            raise ValueError("TSM face ring crosses ownership")
        if (
            Opposite.EdgeIndex != LinkValue.EdgeIndex
            or Opposite.VertexIndex != Following.VertexIndex
            or LinkValue.VertexIndex == Following.VertexIndex
        ):
            raise ValueError("TSM edge endpoints differ")
