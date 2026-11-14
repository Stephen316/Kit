# Timeline groups may have no feature entity

The rolled-back corpus control contains a `ProfileGroup` timeline entry whose `entity` is `None`. Accessing `entry.entity.objectType` fails even though Fusion opens and rebuilds the document correctly. The group reports `isGroup=True`, health value 5 and an empty message.

Record group identity independently and allow a missing entity when observing timeline groups. Require the appropriate concrete entity for actual feature operations. Do not skip or silently remove the group, and do not treat all unknown health states as success.

The [initial observation failure](../../../../../re/Fusion/LocalOracle/RolledHistory/ControlObservation.InitialFailure.json), [corrected observation](../../../../../re/Fusion/LocalOracle/RolledHistory/ControlObservation.json) and [source/reconstructed native comparison](../../../../../re/Fusion/LocalOracle/RolledHistory/NativeAcceptance.json) preserve the evidence. See also [group health behavior](../FusionTimelineGroupHealth.md).
