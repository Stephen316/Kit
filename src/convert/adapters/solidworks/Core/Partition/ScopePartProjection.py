from collections.abc import Sequence
from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Core.Partition.ScopeDesignBody import MakeScopeBody
from convert.adapters.solidworks.Core.Partition.ScopePartOwners import BindScopeAtoms
from convert.adapters.solidworks.Core.Partition.ScopePartPayload import ReadPartBytes
from convert.adapters.solidworks.Core.Partition.ScopedPartition import SplitPartition
from convert.adapters.solidworks.Resolved.Cut.ScopeTypes import ScopedCut, ScopeOwner
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Features.FeatureBody import DesignBody
from interchange.Payloads.PayloadRecord import BrepPayload


# callers receive design bodies and their linked topology only as a complete pair
@Dataclass(frozen=True, slots=True)
class ScopePart:
    Bodies: tuple[DesignBody, DesignBody]
    ModelValue: BrepModel


# scoped projection binds the typed history to the accepted active partition
def ProjectScope(
    Payloads: Sequence[BrepPayload],
    ConfigId: int,
    CutValue: ScopedCut,
    Owners: tuple[ScopeOwner, ScopeOwner],
) -> ScopePart:
    Payload, PayloadData = ReadPartBytes(Payloads, ConfigId)
    AtomMap = BindScopeAtoms(CutValue, Owners)
    DesignIds = {
        AtomId: f"sldprt:body:{BodyId}" for BodyId, (AtomId, _) in AtomMap.items()
    }
    Split = SplitPartition(PayloadData, DesignIds)
    Regions = {Region.RecentAtomId: Region for Region in Split.Regions}
    First, Second = (
        MakeScopeBody(
            ConfigId,
            Payload,
            Regions[AtomMap[Owner.BodyId][0]],
            Owner,
            AtomMap[Owner.BodyId][1],
            CutValue["native_feature_id"],
        )
        for Owner in Owners
    )
    return ScopePart((First, Second), Split.ModelValue)
