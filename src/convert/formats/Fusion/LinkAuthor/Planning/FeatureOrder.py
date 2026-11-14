from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.LinkAuthor.Model.AssemblyPlan import AssemblyPlan

KPlaceMeta = "DcXRefPCIFeatureMetaType"

KPinMeta = "DcGroundOccurrenceFeatureMetaType"

KJointMeta = "DcJointAsBuiltFeatureMetaType"


def FeaturePairs(Scheme: AssemblyPlan) -> tuple[tuple[int, int], ...]:
    Pairs = [(KeySet.FeatureId, KeySet.Feature) for KeySet in Scheme.Places]
    Pairs.extend(
        (Pinning.FeatureId, Pinning.Feature)
        for Pinning in Scheme.Pins
        if Pinning is not None
    )
    if Scheme.Joint is not None:
        Pairs.append((Scheme.Joint.FeatureId, Scheme.Joint.Feature))
    return tuple(sorted(Pairs))


def NodeOrder(Scheme: AssemblyPlan) -> tuple[int, ...]:
    Nodes = {KeySet.Feature: KeySet.NodeId for KeySet in Scheme.Places}
    Features = tuple(PairValue[1] for PairValue in FeaturePairs(Scheme))
    return tuple(
        Identity
        for Feature in Features
        for Identity in ((Nodes[Feature], Feature) if Feature in Nodes else (Feature,))
    )


def IndexMap(Scheme: AssemblyPlan) -> ValueMap[KEntityValue]:
    Counts = (
        (KPlaceMeta, len(Scheme.Places)),
        (KPinMeta, sum(1 for Pinning in Scheme.Pins if Pinning is not None)),
        (KJointMeta, 0 if Scheme.Joint is None else 1),
    )
    return ValueMap(
        tuple(ValuePair(MetaName, Total) for MetaName, Total in sorted(Counts) if Total)
    )
