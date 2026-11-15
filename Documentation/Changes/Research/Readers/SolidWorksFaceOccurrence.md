# P04 SOLIDWORKS face support research reader

Run `python re/solidworks/archive/FaceEvidence.py` from the repository root with Git and the repository Python environment available. The command writes a JSON report for the two licensed discovery captures. It verifies the pinned P04 receipt, independent measurements, native file hashes, full resolved-stream hashes and model generation 19000. It reads the typed face-plane data declaration at the observed boundary and compares decoded orientation, face identity and archive return against the native observations. The report SHA-256 is `1146f564c318bf310e2059b7cec075c107b08473cae29a57f02ca030d651b026`. [Licensed support, nested ownership and face controls](../../../../re/solidworks/records/P04SketchResidence.md#licensed-cut-sketch-support-owner)

| Capture | Face-plane declaration | Typed face token and return | End of support | Plane root (m) | Normal | Primary tuple | Ordered edge occurrences |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| Baseline A | 11,927 | 12,200–12,366 | 12,588 | `(0,0,0.01)` | `+Z` | `(34,1794688208,1)` | `4,1,2,3` |
| YZ | 11,991 | 12,336–12,502 | 12,724 | `(0.01,0,0)` | `+X` | `(34,1794688341,1)` | `4,3,2,1` |

Both walks start at next index 459, allocate `moFaceRefPlnData_c` at slot 460 and `moCompFace_c` at 462, resolve the nested `moFaceRef_c` at slot 464 and finish at next index 475. The replay supplies the earlier map entries as inputs. The native map observations independently confirm classes 350 `moFR_c`, 372 `moFaceRef_c`, 374 `moEndFaceSurfIdRep_c`, 377 `moFromSktEntSurfIdRep_c` and filed object 353 `moExtObject_c` in both captures. Their normalized witness digests are `b42c9fa8fbc0cc5e2799e3d49a9f1717ae213ca8c12939ab4a5ecf7c4bfd40d9` for baseline A and `7a6c1606db89f17e6bd626df49419cc791ff66971ca9699f3e150d30002f3124` for YZ. The shared root part and unit component are available from the [earlier archive map evidence](../../../../re/solidworks/records/P04SketchGap.md#derive-the-interval-offline).

## Source layout

The executable pins are for build `34.4.1.1011`. `moFaceRefPlnData_c` at `sldmodu+0x112e7c0` invokes the geometry loader at `0x1138930`. It reads the point and normal, the optional transform basis, the translation and scale, and optional typed children. Its `moCompFace_c` uses the local unit component and part, the guarded component base, and the modern face read at `0xa63e98`. The enclosing face-plane wrapper repeats the point and normal and ends with the zero outer axis code.

`moFaceRef_c` dispatches its six inline entity IDs through `0xa62f6d`. The selected method at `0xa67e50` reads a typed object at `0xa67f1c`. The surface ID base invokes the embedded reference loader at `0xa67a84`. Its local branch reads a null object at `0xa6859d` and a typed `moFR_c` at `0xa685b2`. The feature reference reads the existing filed object, a signed feature ID and a compact native time word. The filed object establishes the reference context while the feature ID identifies the boss.

`moEndFaceSurfIdRep_c` reads the signed occurrence and one additional dword at `0xa6af81` and `0xa6af8e`. Each subsequent `moFromSktEntSurfIdRep_c` reads one signed boundary index at `0xa69977`. The primary feature ID, time and occurrence begin at face body +46. The corresponding four edge tuples begin at +70, +90, +110 and +130. The last entity pointer is null before the modern trailer. The separately measured supporting cap has occurrence 1, and the opposing cap has occurrence 0. [All eleven supporting face comparisons](../../../../re/solidworks/records/P04SketchResidence.md#supporting-face-occurrence-control)

This is an offline research replay. Product integration requires deriving the earlier map and reaching the face-plane declaration through the resolved profile and `moRefPlane_c` serialization.
