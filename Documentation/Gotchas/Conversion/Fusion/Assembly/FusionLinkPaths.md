# Root links contain local file paths

## Expectation

An exported F3D identifies a referenced design only by cloud identities.

## Actual behavior

Each root manifest link has three UTF-16 paths before its properties.

| Typed field | Observed content |
| --- | --- |
| `ManifestLink.SourcePath` | The absolute path of the export target file |
| `ManifestLink.CachePath` | The local Fusion cache file of the referenced design, named `_<name>.<GUID>.f3d` |
| `ManifestLink.XrefPath` | The cache file in the `_XRef_` folder, named `_<name>.<GUID>_LV<version>.f3d` |

The cache paths contain the home folder and the Fusion cache key of the exporting user.
The `_LV` number follows the referenced version.
It changed from `_LV1` to `_LV2` after Part A version 2 and `updateAllReferences`.

## Workaround

Replace these paths before you commit a native control.
Keep the length of each replacement equal to the original length.
`Sanitize.py` replaces them with `/synthetic/...` text and replaces the home folder and the cache key.
Run `ScanPrivate.py` on each fixture before you commit it.

## Evidence

- [Sanitizer](../../../../../re/Fusion/Reconstruction/LinksConfigs/Sanitize.py)
- [Privacy scanner](../../../../../re/Fusion/Reconstruction/LinksConfigs/ScanPrivate.py)
- [External references change](../../../../Changes/Fusion/Assembly/FusionExternalReferences.md)
