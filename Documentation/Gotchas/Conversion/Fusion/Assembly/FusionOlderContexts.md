# A version context can name an older version of its link

## Expectation

The `VersionUrn` of a version context equals the `URL` of its root manifest link.

## Actual behavior

Member 3 of `re/Fusion/examples/.f3z/example1.f3z` has 8 links. The `URL` of one link names version 12. The Design, ACT and Browser segments each hold a context for that link that names version 11 of the same lineage. The other 21 contexts name their link's version. The copy in `re/Fusion/LocalOracle/Bundles` is the same.

Kit raised `ValueError("Fusion version context disagrees with its link")`.

## Workaround

`CheckDocLinks` accepts a context URN that equals the link URN, or that names a lower version of the same URN. `IsOlderUrn` compares the part before `?version=` and the decimal versions. Any other mismatch still fails.

Every other corpus document passed the equality check, so no other document has an older context.

## Evidence

- [Cache and package notes](../../../../../re/Fusion/Reconstruction/ReadGaps/CachePackageNotes.md#version-contexts-older-than-their-link-member-3)
- [Link spy](../../../../../re/Fusion/Reconstruction/ReadGaps/LinkSpy.py)
- [Cache gap tests](../../../../../tests/convert/formats/FusionCodec/SavedCorpus/CacheGapTests.py), case `TestOlderUrn`
- [Link renewal](FusionLinkRenewal.md)
