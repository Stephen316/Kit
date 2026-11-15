# Fusion inspection needs ZIP Zstandard support

The SDK supports Python 3.11, which can suggest that every inspection view supports it.
Fusion archives can contain ZIP method 93 members.
[Python ZIP Zstandard support](https://docs.python.org/3.14/library/zipfile.html#zipfile.ZIP_ZSTANDARD) was added in Python 3.14.

The CLI therefore requires Python 3.14 for Fusion stream extraction and native inspection.
Container inventory remains available on older interpreters because it does not inflate members.
Install the tool with `uv tool install --python 3.14 .` for all Fusion inspection views.

The guard lives in `FusionView` and `DecodeFile`; the SDK callback contracts remain unchanged.
This records source inspection, not a locally executed decode.
