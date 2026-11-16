# Capture a face-supported SOLIDWORKS two-pad grid

The historical [two-pad experiments](../../../../re/solidworks/corpus/CorpusTwo.md#54-twopad--second-pad-depth-3--5--8-mm-face-supported) establish an editable native reference design. The corpus index has no hash-bound copy of those original native files. This capture creates fresh controls through the licensed SOLIDWORKS API for the A09 codec investigation.

The lower pad is 40 × 20 mm and the upper pad is 10 × 10 mm. The upper sketch selects the lower boss's native top face. The grid contains two independently authored 10 mm + 5 mm baselines, upper depths of 3 and 8 mm, and a base depth of 11 mm. The upper boss merges into one solid.

The two-pad collector runs from its [pinned source](https://github.com/Stephen316/Kit/commit/463a3de14e4cb34aeeaa6aed1aa1e8b2804572c8) in a separate checkout. Use the signed-in Windows desktop with SOLIDWORKS stopped, the shared exclusive oracle lease, and an unused private output directory outside the checkout. Run under Windows PowerShell 5.1 with its normal module path.

```powershell
powershell.exe -NoProfile -STA -File re/automation/PairedCaptures/SolidWorksAuthoring/RunTwoPad.ps1 -OutputDirectory PATH -SourceRevision 463a3de14e4cb34aeeaa6aed1aa1e8b2804572c8
```

The collector measures healthy controls around both phases. It records saved hashes, the live feature tree and driving dimensions, the upper sketch's resolved supporting face, body topology, volume and centroid. It compares volume and center to the independent stacked-prism formula. In the fresh reopen process it edits the upper depth, edits the base depth so the supporting face moves, and restores both. The original save hashes must stay unchanged. [SOLIDWORKS extrusion API](https://help.solidworks.com/2024/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IFeatureManager~FeatureExtrusion2.html)

## Verified native discovery

The licensed run on SOLIDWORKS `34.4.1.1011` used fresh COM-owned processes 39572 and 35076. Both exited with code 0. Four byte-identical stock controls matched the original SHA-256, single body, volume and centroid. All five discovery saves opened and rebuilt with zero load errors or warnings. Each retained one solid with 11 faces, 24 edges and 16 vertices. The saved hashes were unchanged after reopen and measurement.

| Reopened case                      | Volume (mm³) | Center Z (mm) | Upper sketch support Z (mm) |
| ---------------------------------- | -----------: | ------------: | --------------------------: |
| Baselines A and B                  |        8,500 |      5.441176 |                          10 |
| Upper depth 3 mm                   |        8,300 |      5.234940 |                          10 |
| Upper depth 8 mm                   |        8,800 |      5.818182 |                          10 |
| Base depth 11 mm, upper depth 5 mm |        9,300 |      5.930108 |                          11 |

In the fresh reopen process, editing only the upper depth from 5 to 7 mm increased volume from 8,500 to 8,700 mm³. Editing only the base depth from 10 to 11 mm increased volume to 9,300 mm³ and moved the upper sketch to the base boss's top face at Z=11 mm. Restoration returned the volume to 8,500 mm³ and the support to Z=10 mm. The retained report binds the original archive hashes to the two processes, four stock controls and 18 geometry observations.

The native report SHA-256 is `bf0d74c06878c6c5063e4b9a55c61c2ef258bdc24323adbfb8f8d069bc77697e`. The independent source, archive, process and geometry audit SHA-256 is `dc90e21c9a5511a9048fe48446ceff837dded6c0b5441973d1d5916b45657a06`. The earlier direct-launch attempt saved four files and stalled while closing its stock control. Its incomplete artifacts remain separate from the accepted COM discovery run. [Paired corpus harness](../../../Gotchas/Research/Workers/PairedHarnessAuditPin.md)

The strict SDK read at `4e52bd27` recovered the upper boss depth, its four-sided profile and its ownership of the final solid on all five saves. The upper sketch projected onto the principal plane at Z=0 with no face selection. The licensed readback resolved its support to the base boss at Z=10 or Z=11 mm. The scoped discrepancy report SHA-256 is `5466359de266aaa4291d76d8df87a071f11088d3cd178ce539095542273d8453`.

The typed archive face record and the native persistent reference identify the same base cap and four ordered boundaries in all five cases. The saved sketch pose matches the reopened native model-to-sketch transform. The bounded archive probe found the support record within the resolved stream after reaching the base boss. The upper sketch's complete object-allocation walk still stops at its type-14 line relation. The archive support receipt SHA-256 is `a75e915f185990ca45958e3cae2c2796e57d34a0f76ade734a8875e4ebca71da`.

A09 still needs typed ownership through the full archive, donor-free reproduction, and licensed validation of the generated part.
