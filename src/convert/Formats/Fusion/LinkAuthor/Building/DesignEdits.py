from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.LinkAuthor.Edits.RecordEdit import (
    AppendItems,
    MarkFrame,
    ReadValue,
    WriteValue,
)
from convert.Formats.Fusion.LinkAuthor.Model.AssemblyPlan import AssemblyPlan
from convert.Formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.Formats.Fusion.LinkAuthor.Planning.FeatureOrder import (
    FeaturePairs,
    IndexMap,
    NodeOrder,
)
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the local items contract needs a shared interpretation so cross document references retain their intended ownership
def LocalItems(Identities: tuple[int, ...]) -> tuple[LocalRef, ...]:
    return tuple(LocalRef(Identity) for Identity in Identities)


# the edit places contract needs a shared interpretation so cross document references retain their intended ownership
def EditPlaces(
    Records: tuple[EntityRecord, ...], RootInfo: RootFacts, Scheme: AssemblyPlan
) -> tuple[EntityRecord, ...]:
    Instances = LocalItems(tuple(KeySet.Instance for KeySet in Scheme.Places))
    Occurrences = LocalItems(
        tuple(
            Identity
            for KeySet in Scheme.Places
            for Identity in (KeySet.Occurrence, *KeySet.Nested)
        )
    )
    Overrides = LocalItems(
        tuple(Pinning.Extra[0] for Pinning in Scheme.Pins if Pinning is not None)
    )
    Records = WriteValue(
        Records, RootInfo.Component, "operationSeedId", Scheme.FeatureNext
    )
    Records = WriteValue(
        Records, RootInfo.Component, "rXRefManager", LocalRef(Scheme.XRefId)
    )
    Records = AppendItems(Records, RootInfo.Instances, "children", Instances)
    if Overrides:
        Records = MarkFrame(Records, RootInfo.Instances)
    Records = AppendItems(Records, RootInfo.InstancesRoot, "rooted", Instances)
    Records = AppendItems(Records, RootInfo.Fragment, "occurrences", Occurrences)
    return AppendItems(Records, RootInfo.Overrides, "children", Overrides)


# edit features needs an explicit validity boundary so cross document references retain their intended ownership
def EditFeatures(
    Records: tuple[EntityRecord, ...], RootInfo: RootFacts, Scheme: AssemblyPlan
) -> tuple[EntityRecord, ...]:
    Pairs = FeaturePairs(Scheme)
    if ReadValue(Records, RootInfo.Fragment, "featureIndexMap") != ValueMap(()) or (
        ReadValue(Records, RootInfo.FeatureIds, "featureIdMap") != ValueMap(())
    ):
        raise ValueError("Fusion assembly authoring needs a base without features")
    Features = ValueMap(tuple(ValuePair(First, Second) for First, Second in Pairs))
    Records = WriteValue(
        Records, RootInfo.Fragment, "featureIndexMap", IndexMap(Scheme)
    )
    Records = WriteValue(Records, RootInfo.FeatureIds, "featureIdMap", Features)
    Records = AppendItems(
        Records, RootInfo.NodesId, "children", LocalItems(NodeOrder(Scheme))
    )
    return AppendItems(
        Records,
        RootInfo.CreationOrder,
        "representationFeatures",
        LocalItems(tuple(PairValue[1] for PairValue in Pairs)),
    )


# edit joint needs an explicit validity boundary so cross document references retain their intended ownership
def EditJoint(
    Records: tuple[EntityRecord, ...], RootInfo: RootFacts, Scheme: AssemblyPlan
) -> tuple[EntityRecord, ...]:
    if Scheme.Joint is None:
        return Records
    JointId, DcOccurId, JointOccId = (
        Scheme.Joint.Extra[0],
        Scheme.Joint.Extra[10],
        Scheme.Joint.Extra[11],
    )
    for Owner, Child in (
        (RootInfo.Constraints, JointId),
        (RootInfo.ConstraintOccs, JointOccId),
    ):
        if ReadValue(Records, Owner, "children") != ValueSeries(()):
            raise ValueError("Fusion assembly authoring needs a base without joints")
        Records = AppendItems(Records, Owner, "children", (LocalRef(Child),))
        Records = WriteValue(Records, Owner, "highWaterMark", 1)
    return AppendItems(
        Records,
        RootInfo.RootOccurrence,
        "dcAssyConstraintOccurrences",
        (LocalRef(DcOccurId),),
    )


# the edit design contract needs a shared interpretation so cross document references retain their intended ownership
def EditDesign(
    Records: tuple[EntityRecord, ...], RootInfo: RootFacts, Scheme: AssemblyPlan
) -> tuple[EntityRecord, ...]:
    return EditJoint(
        EditFeatures(EditPlaces(Records, RootInfo, Scheme), RootInfo, Scheme),
        RootInfo,
        Scheme,
    )
