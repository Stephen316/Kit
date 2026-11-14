# Registered writers join the swap matrix check

A writer that accepts only its own qualified documents might appear to be outside the cross-format swap tests.
`TestSFMRADK` in `tests/convert/formats/SwapsTests.py` requires every extension that a registered reader and a registered writer share to be in the swap matrix.
The Fusion writer accepts only documents with `fusion.authoring` or `fusion.native_state` metadata, so it cannot write the SolidWorks, FreeCAD or CATIA swap sources.

Exclude such a format by its format identifier in that check, as for `interchange.json`.
Add a format to the swap matrix when its writer accepts documents from the other formats.
See [the qualified Fusion adapter](../../Changes/Fusion/Adapter/FusionPublicAdapter.md).
