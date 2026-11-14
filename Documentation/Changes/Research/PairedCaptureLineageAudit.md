# Paired capture lineage audit

This audit checked the committed Git objects at `8bb7c9bdda2027b190932f8502b6a305188ce560` on Kit PR #94. It verified capture bytes, provenance and observation coverage. No CAD application or Kit reader ran during the audit.

## Capture inventory

| Recipe | Family and split | Fusion receipt | SOLIDWORKS receipt | Files per vendor |
| --- | --- | --- | --- | ---: |
| P01 | Rectangular history, discovery | [Fusion](../../../re/automation/PairedCaptures/P01/fusion-5dc3245eb59c/receipt.json) | [SOLIDWORKS](../../../re/automation/PairedCaptures/P01/solidworks-75b9308cf13e/receipt.json) | 6 |
| P02 | Circular sketch, qualification | [Fusion](../../../re/automation/PairedCaptures/P02/fusion-5f51e2cceed1/receipt.json) | [SOLIDWORKS](../../../re/automation/PairedCaptures/P02/solidworks-4a9e35f34a39/receipt.json) | 5 |
| P03 | Rectangular history, discovery | [Fusion](../../../re/automation/PairedCaptures/P03/fusion-8d53584027ff/receipt.json) | [SOLIDWORKS](../../../re/automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json) | 8 |
| P04 | Rectangular history, discovery | [Fusion](../../../re/automation/PairedCaptures/P04/fusion-9cf53a55ea8b/receipt.json) | [SOLIDWORKS](../../../re/automation/PairedCaptures/P04/solidworks-c1986308375a/receipt.json) | 11 |
| P05 | Annular revolution, holdout | [Fusion](../../../re/automation/PairedCaptures/P05/fusion-108829955958/receipt.json) | [SOLIDWORKS](../../../re/automation/PairedCaptures/P05/solidworks-c3d4361662e0/receipt.json) | 7 |

Each of the ten receipts matches the SHA-256 of its committed measurements. The two records agree on save order, file names and hashes. The 74 native Git blobs match their recorded SHA-256 and byte counts, and the paired capture tree contains only listed native files. Both vendors' records match the SHA-256 of [PairSpecs.json](../../../re/automation/PairSpecs.json), `3c93e024f9fbdda50e610bda3b363bf30e8e7cdc914ef0728087befe129951bf`, and each recipe's canonical JSON digest. The before and after control hashes match their Git blobs. The Fusion control reports one body and 30,000 mm³, and the SOLIDWORKS control reports one body and 881,814.3482038013 mm³ before and after each case.

Hashing all 1,914 tracked native files at the audited revision found no matching bytes for any capture at another path. The 778 native files in the pinned historical corpus had no matching capture hashes. No capture blob was reachable from the parent of its introduction commit. This covers recorded Git objects. Off-repository sources and semantically equivalent earlier models remain outside the exact-byte check.

Keep all 50 discovery files, 10 qualification files and 14 holdout files with their respective families. Reserve both P05 groups and all their descendants for frozen-rule evaluation. P05 contributed only inventory, hash, provenance and recording-coverage information to this audit.

## Authoring provenance

The Fusion capture generators match the receipt digests at their introduction commits. P01 used a standalone generator at `b563ec10`. P02, P03 and P05 used the shared helper at `96ae0066`, with SHA-256 `deb2437a77658f976a03e27596bc56b39bc52c4cee6afde628e6601b84b817b1`. P04 used the helper at `f299293e`, with SHA-256 `afb47d9939aad5892c770ba127e50633cc78349a815849121a8ae66533a3771e`. The generators create fresh parametric designs through Fusion's API. They open the existing control for measurement, then reopen only archives exported by the current run.

All SOLIDWORKS captures were introduced in `8bb7c9bd` and bind the specification at `777a8ac77ee509ace6d349a14bdb11386f6be0bb`. The audit matched the local first-save and raw measurement records to the committed observations and save hashes. The local authoring harness uses the SOLIDWORKS API to create and measure new parts and reopen the resulting saves. The harness remains outside Git, so an independent checkout can verify the published receipt and native file bytes. Replaying the generation requires retaining and pinning the harness. [SOLIDWORKS capture entry](SolidWorksPairedCaptures.md)

## Qualification limits

- SOLIDWORKS 2026 records API revision `34.4.1` and executable build `34.4.1.1011`. The first and second process IDs differ, with a recorded restart before the repeat baseline save. The second process reopened and rebuilt all 37 parts with zero recorded open errors or warnings. The independent measurements support bounded reader comparisons of sketch geometry, dimensions, relation participants, edit and restore responses, operations and suppression. Complete edge-to-dimension bindings and stable supporting-face identity are absent from the measurement schema. The P04 cut records a face support type, equations and edit responses, with a null support name.
- Fusion build `2706.1.17` records a baseline-A archive reopen and recompute plus readbacks of the edited and variant exports. This covers 32 of 37 native files. Each baseline-B export lacks its own readback. All five measurement files identify the same Fusion process as the authoring and reopening process. Imports record successfully returned documents and feature health. Explicit load errors and warnings were not recorded.
- Fusion records sketch constraint and dimension types without full participant or target bindings. P04 identifies the support as a face and records the API message that reading its identity requires a timeline rollback. The capture edit responses and generator show the intended construction, and an exact supporting-face identity remains unobserved at readback. [Fusion face reference behavior](../../Gotchas/Conversion/Fusion/Api/FusionFaceSketchReferencePlane.md)
- The pinned historical manifest predates these captures, and the corpus gate still reports zero qualified pairs. Capture intake must bind the verified receipts to their recipe and whole-family reservations. Existing imported-family reservations remain provisional.

To close A02d, record a Fusion repeat save across an application restart and bind the resulting readbacks, including baseline B and load diagnostics, to exact file hashes. Collect participant, dimension target and P04 parent face identities wherever a qualification claim relies on those observations. Retain the SOLIDWORKS authoring harness and pin its reviewed source. A04c can already compare bounded independent SOLIDWORKS observations, starting with the discovery family and reserving P02 for qualification. [Step register](../../Reference/Research/AutomationSteps.md#a02-implementation-and-remaining-evidence)
