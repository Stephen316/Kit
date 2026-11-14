# Scenes can hold a protein effect attribute

## Expectation

Appearance assets reach a scene through `FPrioritizedProteinAttribute`.

## Actual behavior

Member 5 of `re/Fusion/examples/.f3z/example1.f3z` holds one `FProteinEffectAttribute`. No other corpus world holds the class, apart from the copy in `re/Fusion/LocalOracle/Bundles`.

It sits in a child set with `IsSpecific` 1 and flags `0x20`. After the priority and tie flag, it holds one UTF-16 text: an appearance asset id of 36 characters. The child set's apply types follow.

Kit had no field rule for the class. It raised `ValueError("Unsupported graphics attribute class: FProteinEffectAttribute")`.

## Workaround

Read `FProteinEffectAttribute` as one `AssetReference` text field, like the first field of `FPrioritizedProteinAttribute`.

## Evidence

- [Cache and package notes](../../../../../re/Fusion/Reconstruction/ReadGaps/CachePackageNotes.md#protein-effect-attribute-member-5)
- [Cache gap tests](../../../../../tests/convert/formats/FusionCodec/SavedCorpus/CacheGapTests.py), case `TestCacheMember`
