from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismFrame import ReadPrismFrame
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismGraph import ReadPrismGraph
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismRoles import ReadPrismRoles
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismTags import ReadPrismTags
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.MapSolid import (
    MapSolid,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.MapSolidTags import (
    MapSolidTags,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadSolid(Table: AsmTable) -> tuple[PrismFrame, PrismTags, dict[int, int]]:
    Graph = ReadPrismGraph(Table)
    Roles = ReadPrismRoles(Graph)
    SolidMap = MapSolid(Table, Graph, Roles)
    TagMap = MapSolidTags(Table, SolidMap)
    Frame = ReadPrismFrame(Table, Graph, Roles, SolidMap)
    Mapping = {0: 0, 1: 1, 2: 2, 3: 3}
    Mapping.update(
        {Index + 2: Identity for Index, Identity in SolidMap.items() if Index >= 2}
    )
    Mapping.update({Index + 50: Identity for Index, Identity in TagMap.items()})
    return Frame, ReadPrismTags(Table, TagMap), Mapping
