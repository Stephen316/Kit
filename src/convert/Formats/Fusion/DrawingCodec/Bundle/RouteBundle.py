from collections.abc import Callable

from convert.Formats.Fusion.BundleCodec.Model.FusionBundle import FusionBundle
from convert.Formats.Fusion.BundleCodec.ReadBundle import ReadBundle
from convert.Formats.Fusion.DrawingCodec.Bundle.DrawingBundle import DrawingBundle
from convert.Formats.Fusion.DrawingCodec.Bundle.ReadDrawBundle import (
    ReadDrawBundle,
)


# the route bundle contract needs a shared interpretation so drawing members retain their sheet and model associations
def RouteBundle(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> FusionBundle | DrawingBundle:
    Bundle = ReadBundle(DataValue, InflateZstd)
    Graph = Bundle.Description.Graph
    Owners = {Entry.ObjectId: Entry for Entry in Graph.Objects}
    if Owners[Graph.RootIds[0]].ContentType == "f2d":
        return ReadDrawBundle(DataValue, InflateZstd)
    return Bundle
