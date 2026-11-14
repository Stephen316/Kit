# Paired capture intake

Run the [research intake](../../../re/automation/PairedCaptureIntake.py) from a complete Git checkout. Pass the full commit hash of the candidate to bind.

```sh
python re/automation/PairedCaptureIntake.py --revision "$(git rev-parse HEAD)"
```

The command emits a JSON report. It requires one receipt from each application for each recipe and derives the complete save roster from the recipe's edits and feature history. It checks the committed receipt, measurement, specification and native file hashes, byte lengths and save order. It also checks the control hashes and measurement consistency, the Fusion generator source at each receipt's introduction commit, and the SOLIDWORKS specification at its recorded source revision.

The intake checks exact Git blob aliases anywhere in the candidate tree and older reachable objects at each capture's introduction. It also checks native SHA-256 aliases in the immutable historical corpus manifest. Exact matches outside a capture's family, matches in the historical manifest, and reused prior Git blobs quarantine the entire capture family. All files in the annular revolution family are reserved for frozen-rule holdout evaluation. The intake uses P05 for inventory, hashes, provenance and recording coverage.

| Exit | Meaning |
| --- | --- |
| `0` | Capture intake completed and found no quarantined families |
| `1` | Invalid revision, missing inputs or mismatched evidence |
| `2` | A family was quarantined, or `--require-pairs` found qualification blockers |

The current [lineage audit](PairedCaptureLineageAudit.md) identifies five recipes, ten receipts and 74 native files. The intake checks the [retained SOLIDWORKS source](../../Reference/Research/SolidWorksCaptureAuthoring.md) against the audit digest. Its JSON report records the outstanding application restart, readback, load diagnostic and binding gaps. The historical corpus and its reader inputs retain their own snapshot. Semantic qualification and CAD conversion acceptance use separate checks.

The existing [corpus process check](../../../tests/Research/CorpusFlowTests.py) exercises the intake and verifies the holdout reservation and the blocked qualification status in CI.
