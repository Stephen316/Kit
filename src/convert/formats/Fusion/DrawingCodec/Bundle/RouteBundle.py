from collections.abc import Callable

from convert.formats.Fusion.BundleCodec.Model.FusionBundle import FusionBundle
from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
from convert.formats.Fusion.DrawingCodec.Bundle.DrawingBundle import DrawingBundle
from convert.formats.Fusion.DrawingCodec.Bundle.ReadDrawBundle import (
    ReadDrawBundle,
)


def RouteBundle(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> FusionBundle | DrawingBundle:
    Bundle = ReadBundle(DataValue, InflateZstd)
    Graph = Bundle.Description.Graph
    Owners = {Entry.ObjectId: Entry for Entry in Graph.Objects}
    if Owners[Graph.RootIds[0]].ContentType == "f2d":
        return ReadDrawBundle(DataValue, InflateZstd)
    return Bundle
