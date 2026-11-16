# Generation 19000 rectangle contour trim

`WriteRectTrim` continues the resolved profile after principal support. It takes the emitted profile object, its native feature ID, the four authored perimeter IDs, contour mode, derived timestamp, feature-reference time, file metadata and four ordered native trim side members. It returns the file object the subsequent extrusion may reference.

## Native ownership

The preferred virtual addresses below refer to SOLIDWORKS `34.4.1.1011` `sldmodu.dll`, SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`.

| Field group | Source and observed branch |
| --- | --- |
| Profile flags, optional object and two signed scalars | `moProfileFeature_c` archive slot 5 at `0x4bb1b0b0` saves the transform presence at `0x4bb1b987`, profile flags at `0x4bb1b9c6`, an optional object at `0x4bb1b9f2`, and data members `+0x11c` and `+0x118` at `0x4bb1ba04` and `0x4bb1ba1a`. The data constructor at `0x4c0c8186` through `0x4c0c81b2` supplies flags 4 and signed defaults −1 and 0. Both optional members are absent in the admitted branch. |
| Derived timestamp, profile mode and second optional object | The unsigned value at `0x4bb1ba30` takes the data member `+0x2a0` used by the exported `getDerivedTimeStamp` at `0x4c0d4320`. Its constructor value is 101 at `0x4c0c8289`. The captures save 103–111, so this is caller state. The narrow mode at `0x4bb1ba40` is 0 for P01 and 1 for P03. The optional pointer at `0x4bb1ba68` is null in these captures. |
| Surface and segment lists | Virtual saves at `0x4bb1ba81` and `0x4bb1ba98` use the enclosing data lists at `+0x128` and `+0x148`. The compact branch saves one `moSimpleSurfIdRep_c` with occurrence zero, then four segment IDs, twice per side class. The surface's archive slot at `0x4bba9930` and the shared side serializer at `0x4bba7990` call `0x4bba7a20` before their signed member writes. The surface emits `+0x38` at `0x4bba9962`. The side classes emit `+0x38` and `+0x3c` at `0x4bba79bd` and `0x4bba79d8`. Their measured trailing member is zero. |
| Feature and file ownership | All representatives alias the same profile object. Each allocates a distinct `moFR_c`, whose archive slot at `0x4bb34180` stores the file pointer at `0x4bb341d4` and calls the feature ID and compact time codec at `0x4bb341e1`. The compact feature time is filed at `0x4bb33e9c`. The surface allocates the standalone file and its two string handles. The segments alias this exact file and carry the same feature ID and reference time. [Shared file layout](CmgrTail.md) |
| Profile return | The final signed word is the profile member `+0x42c`, written at `0x4bb1bad3` and zero-initialized at `0x4c0c8787`. |

## Receipt-pinned evidence

| History | Trim start | Trim end | Next archive slot | File object |
| --- | --- | --- | --- | --- |
| P01, six saves | Front 11526, Right 11598 | Front 11895 or 12125, Right 11967 | 231 → 250 | 236 |
| P03, eight saves | Front 11625, Right 11697 | Front 11994, 11996 or 12224, Right 12066 | 238 → 257 | 243 |

The production `ReadRectTrim` reaches the resolved list footer in P01 and the schema-1 `moExtrusion_c` definition in P03. Both histories add six class and thirteen object slots. The reopened native sketch profiles independently corroborate the four line IDs and the continuity of each ordered trim loop. Four side-and-edge orders and two standalone file path/flag forms occur across the 14 licensed saves. Side selection and enumeration remain explicit caller state. Geometry-only derivation of that ordered state requires separate evidence. Saved file path strings remain private.

Run `python -B re/solidworks/WriterResearch/VerifyRectTrim.py --read-only` in the Kit environment. The 14 receipt-pinned rows yield `trim_replay_sha256` of `772dc555b6cfbe4264ca8701b15da6787d881f3496457c2c816953fb13bf511c`. Hosted `CheckRectTrim` checks the constructed bytes and returned archive map in addition to this read-only evidence. Complete generated-part native open, rebuild and driving edit evidence is pending.

Hosted `CheckProfile` passes one writer and its live object map through the system owners, sketch, support and contour trim. It appends the four-byte resolved-list footer for P01 and stops at the boss entry for P03. Dimension display comparison uses the documented normalization for inactive fields. [Profile composition verifier](VerifyAuthoredProfile.py), [display field evidence](RectangleDisplays.md)
