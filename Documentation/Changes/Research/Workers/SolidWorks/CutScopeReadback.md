# Two-body through-all cut scope evidence

The discovery control uses two separate bodies and a single rectangular Cut from the upper cap of body A. The downward profile intersects both bodies. The three input choices are automatic, explicit A, and explicit A+B. The specification predicts volumes of 8,000 and 1,000 mm³ before cutting, and 7,200 and 600 mm³ for A and B when both are cut. Explicit A leaves the 1,000 mm³ body B intact.

## Compare saved native observations

Copy the application report and its three native archives into one directory per application. Include the Fusion Phase B receipt alongside its report. Supply the exact report digest from each retained run. Both source revisions must be present in Git when comparing the two applications.

```text
python re/automation/CutScopeEvidence.py --solidworks <report.json> --solidworks-sha256 <digest> --fusion <report.json> --fusion-sha256 <digest>
```

Either application may be compared independently. The script verifies archive hashes and sizes, the Git-pinned specification and producer sources, and a distinct fresh reopen. It checks body ownership, bounds, volume, centroid and face, edge and vertex counts before the cut and at each saved, reopened and rebuilt observation. The before-cut control identifies the unchanged body in the A-only case. Results for automatic and explicit A+B keep their observed policy separate from equality of the measured geometry.

The SOLIDWORKS result retains the raw Feature Scope and Auto-select values and the scope-body references returned by the native API. The canonical extent is through-all, one direction, with a null depth. Fusion's resolved participants can verify the affected set even when the native getter leaves the authored policy unobserved. Scope policy, measured result geometry and editable cross-format acceptance each require their own evidence.

## SOLIDWORKS archive leads

The bounded P04 single-body through-all control provides exact typed boundaries for investigating the new multibody archives. The offsets below are byte positions in its MO 19000 `Contents/Config-0-ResolvedFeatures` stream with SHA-256 `26341c83246d7a3088bb4ea44ecc978f56ebad2d4ceb6ee72942b090c1c506e4`.

| Byte offset | Typed record or field | Witnessed value |
| ---: | --- | --- |
| 12,993 | `moICE_c` cut node | Native feature ID 46 |
| 13,211 | Counted atom framing and atom-body type | `(1, 102, 3)` |
| 13,223 and 13,227 | Scope body array presence and count | `i32 1`, `u16 1` |
| 13,229 | `moCompSolidBody_c` through byte 13,527 | Body ID 101, producer feature ID 34 |
| 13,527 | Feature scope scalar | `i32 1` |
| 14,008 and 14,230 | Primary and repeated chooser `su_CDWordArray` counts | Both zero |
| 14,238 | Additional chooser presence, expanded scope, second scope array presence and partition presence | `(0, 0, 0, 1)` |
| 14,320 and 14,346 | `moEndSpec_c` and its depth selector | `(1, 0)` end conditions, null depth slot |

In the matched `sldmodu.dll`, SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`, the atom feature loader invokes the counted array helper at RVA `0x9cabbc` for object field `+0x548`. It immediately reads the signed feature scope scalar into `+0x544` at `0x9cabe8`. The exported accessor at `0x1467f0` returns this same scalar. The expanded scope accessor at `0x14d890` returns `+0x578`, which the loader reads at `0x9cafd8` just before the second array at `0x9cb013`.

The blind baseline has the same atom-body type 3, one typed scope body, scope scalar 1 and both zero chooser counts. The existing reader guards these single-body shapes. The Auto-select accessor at RVA `0x143250` reads object field `+0x558`. Its persistence remains unresolved because the reviewed atom feature archive path has no direct read of that field. [Cut operation reader](../../../../../src/convert/adapters/solidworks/resolved/cut/CutOpRead.py) · [Chooser body-list grammar](../../../../../re/solidworks/records/FeatureBody.md#5-moice_c--the-former-96-kb-content-wall-is-structurally-closed)
