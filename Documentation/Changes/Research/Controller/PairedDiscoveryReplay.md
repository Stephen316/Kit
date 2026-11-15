# Replay the paired discovery grid in A03

Use the `candidate.paired-discovery` runner to decode the existing P01, P03 and P04 experiment variants and repeat saves, including each application's independently saved baselines. The runner uses the candidate's public readers and compares their output to the application observations pinned by the capture receipts. It also checks the separate licensed SOLIDWORKS readbacks from before and after rebuild.

Register Python 3.14 or newer with the candidate's runtime dependencies. Use `re/automation/StageEleven.py` as the script followed by the whole-argument `{session}` substitution and `re/automation/StageElevenResult.json` as the result schema. Run from the clean candidate checkout and set `options.candidate_revision` to its full Git commit.

Bind the trusted readback files to these input roles before submitting the job.

| Role | Input file |
| --- | --- |
| `principal-dispatch` | P01/P03 `dispatch.json` |
| `principal-plan` | P01/P03 `readback.plan.json` |
| `principal-measurements` | P01/P03 `readback.measurements.json` |
| `principal-receipt` | P01/P03 `readback.receipt.json` |
| `cut-plan` | P04 `plan.json` |
| `cut-measurements` | P04 `measurements.json` |
| `cut-receipt` | P04 `receipt.json` |
| `ci` | Pending CI JSON with the exact revision |

Give each candidate job its own `ci` binding with a pending input like this.

```json
{"candidate_revision":"FULL_COMMIT_SHA","schema":1,"scope":"p01-p03-p04-paired-reader-discovery","status":"pending"}
```

When all 25 pairs and the comparison controls pass, A03 records `waiting_ci`. The result keeps the save pins and the comparison report digests. On a discrepancy it records `rejected` with the affected checks. The runner uses historical Fusion measurements and leaves fresh licensed Fusion acceptance open. P05 remains reserved for frozen-rule evaluation.

Freeze a [pending CI roster](PendingCiRoster.md) from the parked attempt. Apply the exact successful hosted evidence with the [batch release command](PairedCiBatchRelease.md).

The Windows supervisor ran the pinned candidate at `356e695144471ac45e9e6a5939d4f9ce7efd9d03` and parked attempt one in `waiting_ci` after 16.4 seconds. A03 recorded six P01, eight P03 and eleven P04 pairs with zero counterexamples. The pending roster included the exact attempt and result. Its payload digest is `c1fbeeaf238e0918d27f69eb4eb10ae4640905b0d39d1081877560c115daabd5`.
