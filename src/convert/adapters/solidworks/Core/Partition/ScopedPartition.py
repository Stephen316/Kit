from collections.abc import Mapping
from dataclasses import dataclass as Dataclass, replace as Replace

from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.Partition.PartMass import PartMass
from convert.adapters.solidworks.Core.Partition.PartRegion import ExtractRegion
from convert.adapters.solidworks.Core.Partition.PartRegionCover import CheckPartCover
from convert.adapters.solidworks.Core.Partition.PartRegionOwner import ReadRegionAtoms
from convert.adapters.solidworks.Core.Partition.PartTopology import (
    ActivePartMass,
    PartTopology,
)
from convert.Geometry.Parasolid import DecodeBrepModel, ParaHeaderData
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepBody
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.Records.RecordTopology import TopologyCounts

# this schema carries the checked shell region and named atom layouts
KScopeSchema = "SCH_3701250_37102_13006"


# each linked body retains its provenance identity and geometric measurement
@Dataclass(frozen=True, slots=True)
class ScopedRegion:
    BodyValue: BrepBody
    NativeOwner: int
    NativeRegion: int
    RecentAtomId: int
    Topology: TopologyCounts
    MassValue: PartMass


# whole part topology stays intact while its carrier becomes independently owned bodies
@Dataclass(frozen=True, slots=True)
class ScopedPartition:
    ModelValue: BrepModel
    Regions: tuple[ScopedRegion, ScopedRegion]


# caller design identities are admissible only with exact distinct native atom keys
def CheckDesignIds(DesignIds: Mapping[int, str]) -> None:
    RequireArch(
        len(DesignIds) == 2
        and all(type(AtomId) is int and AtomId > 0 for AtomId in DesignIds)
        and all(Value and Value == Value.strip() for Value in DesignIds.values())
        and len(set(DesignIds.values())) == len(DesignIds),
        True,
        "two distinct stable design IDs keyed by native atom",
    )


# a neutral body may be attached only after its single solid closes and measures
def MeasureRegion(
    ModelValue: BrepModel,
    NativeOwner: int,
    NativeRegion: int,
    RecentAtomId: int,
    DesignId: str,
) -> ScopedRegion:
    (Carrier,) = ModelValue.bodies
    (RegionId,) = Carrier.region_ids
    BodyValue = Replace(Carrier, id=f"{Carrier.id}:{RegionId}", design_body_id=DesignId)
    SolidValue = Replace(ModelValue, bodies=(BodyValue,))
    RequireArch(
        SolidValue.validate(frozenset({DesignId})), (), "valid owned region topology"
    )
    Summary = PartTopology(SolidValue, DesignId, TopologyCounts())
    Topology, MassValue = ActivePartMass(SolidValue, Summary, DesignId)
    if MassValue is None:
        raise ArchiveError("owned region does not measure as a closed planar solid")
    return ScopedRegion(
        BodyValue, NativeOwner, NativeRegion, RecentAtomId, Topology, MassValue
    )


# the split joins typed regions to their owners before binding caller design identities
def SplitPartition(PayloadData: bytes, DesignIds: Mapping[int, str]) -> ScopedPartition:
    CheckDesignIds(DesignIds)
    Header = ParaHeaderData(PayloadData)
    if (
        Header is None
        or Header.schema != KScopeSchema
        or "transmit file (partition)" not in Header.description.casefold()
    ):
        raise ArchiveError("unsupported two-body partition schema")
    ModelValue = DecodeBrepModel(PayloadData)
    if (
        ModelValue is None
        or len(ModelValue.bodies) != 1
        or len(ModelValue.regions) != 2
    ):
        raise ArchiveError("expected one carrier with two solid regions")
    (Carrier,) = ModelValue.bodies
    FirstRegion, SecondRegion = ModelValue.regions
    RequireArch(
        (
            Carrier.transform,
            Carrier.design_body_id,
            Carrier.wire_ids,
            Carrier.vertex_ids,
            ModelValue.wires,
        ),
        (KTransformIdentity, "", (), (), ()),
        "unbound solid partition carrier",
    )
    RequireArch(
        (
            len(Carrier.region_ids),
            set(Carrier.region_ids),
            FirstRegion.solid,
            SecondRegion.solid,
        ),
        (2, {FirstRegion.id, SecondRegion.id}, True, True),
        "carrier owns both solid regions",
    )
    First = ExtractRegion(ModelValue, FirstRegion, Carrier)
    Second = ExtractRegion(ModelValue, SecondRegion, Carrier)
    CheckPartCover(ModelValue, First, Second)
    Owners = ReadRegionAtoms(PayloadData[Header.body_offset :], (First, Second))
    RequireArch(
        {AtomId for _, _, AtomId in Owners.values()},
        set(DesignIds),
        "exact typed body atoms",
    )
    FirstOwner, FirstNativeId, FirstAtom = Owners[FirstRegion.id]
    SecondOwner, SecondNativeId, SecondAtom = Owners[SecondRegion.id]
    FirstValue = MeasureRegion(
        First, FirstOwner, FirstNativeId, FirstAtom, DesignIds[FirstAtom]
    )
    SecondValue = MeasureRegion(
        Second, SecondOwner, SecondNativeId, SecondAtom, DesignIds[SecondAtom]
    )
    Result = Replace(ModelValue, bodies=(FirstValue.BodyValue, SecondValue.BodyValue))
    RequireArch(
        Result.validate(frozenset(DesignIds.values())), (), "valid split partition"
    )
    return ScopedPartition(Result, (FirstValue, SecondValue))
