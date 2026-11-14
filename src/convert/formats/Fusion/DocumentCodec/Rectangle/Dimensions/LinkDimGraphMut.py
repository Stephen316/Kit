from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Rectangle.Dimensions.Graph.DimGraphEdges import (
    DimGraphEdges,
)
from convert.formats.Fusion.DocumentCodec.Rectangle.Dimensions.Graph.DimGraphMap import (
    DimGraphMap,
)


def LinkDimGraphMut(Author: AuthorState) -> None:
    Edges = DimGraphEdges(Author)
    Nodes = [
        "dc_component",
        "sketch_plane",
        "sketch_matrix",
        "width_binding",
        "depth_binding",
        "dc_sketch",
    ]
    if Author.SpecValue.ProfileKind == "cuboid":
        Nodes.extend(
            [
                "profile_region",
                "profile_model",
                "along_binding",
                "taper_binding",
                "extrude_tool",
                "dc_extrude",
            ]
        )
    Author.Change(
        "compute",
        sortIsCurrent=True,
        sortedNodesAll=[Author.Reference(RoleName) for RoleName in Nodes],
    )
    Author.Change(
        "dependency",
        mapsAreCurrent=True,
        predecessorMap=DimGraphMap(
            Author,
            tuple((Target, Source, TypeValue) for Source, Target, TypeValue in Edges),
        ),
        successorMap=DimGraphMap(Author, Edges),
    )
    for RoleName in Nodes:
        DynamicRole = "dynamic" if RoleName == "dc_component" else RoleName + "_dynamic"
        if RoleName in ("width_binding", "depth_binding"):
            DynamicRole = RoleName.replace("_binding", "_dynamic")
        Predecessors = [Source for Source, Target, _ in Edges if Target == RoleName]
        if Predecessors:
            Author.Change(
                DynamicRole,
                predecessors=[
                    {
                        "key": Author.Reference(Predecessor),
                        "value": Author.Policy.TimeStamp,
                    }
                    for Predecessor in sorted(
                        [*Predecessors, RoleName], key=lambda Value: Author.Roles[Value]
                    )
                ],
            )
