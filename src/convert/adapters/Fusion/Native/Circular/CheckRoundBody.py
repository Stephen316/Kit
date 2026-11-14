from convert.adapters.Fusion.Native.Graph.GraphChecks import RequireFields, ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    ObjectFields,
    SeriesItems,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags


def CheckRoundBody(
    Graph: NativeGraph, Context: ExtrudeContext, TagSet: TopologyTags
) -> None:
    Progenitor = Graph.OneClass("BodyProgenitor")
    RequireFields(
        Progenitor,
        {
            "alternativeProgenitor": None,
            "rRefBodyOfTagInherit": None,
            "shareTargetBodyAddress": False,
            "centerOrder": 0,
        },
    )
    Entries = MappingItems(Progenitor.Fields["featureTagOccMap"])
    if len(Entries) != 1 or Entries[0].Second != 1:
        raise ValueError("Native circular body requires one primary-face occurrence")
    Fields = ObjectFields(Entries[0].First)
    Encoded = tuple(TagSet.SideFace.PrimaryId.encode("ascii"))
    if (
        Fields["primary"] is not False
        or SeriesItems(Fields["facePrimIdData"]) != Encoded
        or SeriesItems(Fields["facePrimIdOffsets"]) != (0, len(Encoded))
    ):
        raise ValueError(
            "Native circular body progenitor does not identify its side face"
        )
    Table = ResolveField(
        Graph, Context.SketchFeature, "rProgenitorTable", "ProgenitorTable"
    )
    if SeriesItems(Table.Fields["ProgenitorTagVec"]):
        raise ValueError("Native circular sketch has an unaccounted progenitor")
