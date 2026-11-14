# Keep the empty configuration sidecar boundary

Kit still reads and writes only empty configuration sidecars.
A native attempt to make configured designs failed because of an account restriction.
Kit did not get native evidence for configuration tables, rules, rows or cells.

## Current behavior

| Member | Accepted content | Other content |
| --- | --- | --- |
| `DesignConfigurationTable.<GUID>.dsgcfg` | JSON object `{}` | `ValueError` |
| `DesignConfigurationRule.<GUID>.dsgcfgrule` | JSON object `{}` | `ValueError` |

`ReadConfigPart` raises `Nonempty Fusion configurations require a qualified schema` for a nonempty object.
`CheckDocConfig` checks each sidecar against its Design serializer trigger.
This change does not remove the pin, because no configured variant is qualified.

## Native attempt

The [configuration control script](../../../../re/Fusion/LocalOracle/LinksConfigs/CreateConfigControls.py) ran in Fusion 2706.1.17.
It made a part with a `lengthC` parameter, a body and a cut hole, and saved it to the acceptance project.
It then called `Design.createConfiguredDesign`.

| Step | Result |
| --- | --- |
| `C0_plain` export | 48,973 bytes, SHA-256 `ca0392bb9be055f2bdb06ed9dcbef4946d788ba31bb08b7677cc53f5e64b3590` |
| `Design.createConfiguredDesign` | `RuntimeError: 3 : Cannot create configuration top table as the user is restricted.` |
| Documents open at the end | 0 |

The script did not reach the steps for parameter columns, suppression columns, appearance tables, rows, rule creation or row activation.
[`LinkEvidence.json`](../../../../re/Fusion/LocalOracle/LinksConfigs/LinkEvidence.json) records the sanitized result.

## Corpus check

`FindConfigs.py` scanned 1,063 F3D and F3Z files under `re/Fusion` and `examples`.
It found no configuration sidecar larger than 2 bytes.
The members of the example1 bundle contain `{}` in both sidecars.

## Search for another source

A second pass looked for a configured design that does not need the restricted permission.
It found none.
Kit did not make or copy any configuration record.

| Source | Check | Result |
| --- | --- | --- |
| Fusion app bundle | `ScanAppConfigs.py` opened 232 design files and 21 nested designs | No configuration sidecar in any file |
| Fusion API stubs | Calls in `adsk/fusion.py` that make a configured design | Only `Design.createConfiguredDesign` |
| Fusion API stubs | `Occurrences.addFromConfiguration` | Needs a configured design from the same project |
| Public web | Autodesk help pages and model sites | No configured sample that downloads without a login |
| Other cloud projects | Not searched | The task rules forbid access outside the acceptance project |

The 232 files are 220 fastener templates, 7 sample bundles, 3 offline test files and 2 other designs.
Whether this account can read the table of an existing configured design through the API is not tested, because no configured design was available.

[`AppConfigScan.json`](../../../../re/Fusion/Reconstruction/LinksConfigs/AppConfigScan.json) records the bundle scan with paths relative to the bundle.
The [scan script](../../../../re/Fusion/Reconstruction/LinksConfigs/ScanAppConfigs.py) reads the bundle and writes nothing into it.

## Next step

Run the control script again with an account that can create configured designs.
The script records an export after each table, row, cell, rule and activation step.

## Related information

- [Configuration licence gotcha](../../../Gotchas/Conversion/Fusion/Configuration/FusionConfigurationLicense.md)
- [External references change](../Assembly/FusionExternalReferences.md)
