from collections import Counter
from collections.abc import Sequence

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from interchange.brep.Curves.BrepCurves import BrepEntity
from interchange.brep.Topology.BrepModel import BrepModel


# topology tables define the independently owned portion of each region
def TopologyTables(ModelValue: BrepModel) -> tuple[Sequence[BrepEntity], ...]:
    return (
        ModelValue.regions,
        ModelValue.shell_uses,
        ModelValue.shells,
        ModelValue.face_uses,
        ModelValue.faces,
        ModelValue.loops,
        ModelValue.coedges,
        ModelValue.edges,
        ModelValue.vertices,
    )


# geometry records may be shared but must still be reachable from the solid shells
def GeometryTables(ModelValue: BrepModel) -> tuple[Sequence[BrepEntity], ...]:
    return ModelValue.curves, ModelValue.pcurves, ModelValue.surfaces


# a region split must account for every topology entity exactly once
def CheckPartCover(ModelValue: BrepModel, First: BrepModel, Second: BrepModel) -> None:
    for Source, LeftTerms, RightTerms in zip(
        TopologyTables(ModelValue),
        TopologyTables(First),
        TopologyTables(Second),
        strict=True,
    ):
        RequireArch(
            Counter(Value.EntityId for Value in (*LeftTerms, *RightTerms))
            == Counter(Value.EntityId for Value in Source),
            True,
            "disjoint complete partition topology",
        )
    for Source, LeftTerms, RightTerms in zip(
        GeometryTables(ModelValue),
        GeometryTables(First),
        GeometryTables(Second),
        strict=True,
    ):
        RequireArch(
            {Value.EntityId for Value in (*LeftTerms, *RightTerms)}
            == {Value.EntityId for Value in Source},
            True,
            "complete partition geometry references",
        )
