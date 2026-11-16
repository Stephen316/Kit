# Saved SOLIDWORKS active partition

The public reader selects the partition stream belonging to the resolved active configuration. A decodable profile packet in that configuration's feature stream can represent its sketch cache. The active partition is the saved part body. The reader retains both native payloads and links a unique typed active body to the neutral design body.

An unreadable or missing active stream leaves the typed part body absent when configuration streams or verified feature history identify the selected partition. Retained profile payloads remain available for inspection. The reader links an active solid to the design body when the archived rectangle Boss or Cut history establishes the body owner. Legacy sheet payloads keep their standalone topology.

The eleven P04 active partitions contain one closed solid. The blind files decode to eleven faces and the through-all file to ten. All have 24 edges and sixteen vertices. Saved planar faces and linear edges supply the axis bounds, including the YZ rotation and the three outer-size edits. The counts and bounds agree with independent native reopening. [Historical body comparison](../Comparison/HistoricalCutBodyEvidence.md), [public archive checks](../../../../../tests/Research/Archives/ArchiveEvidenceTests.py)

The saved oriented loops also supply volume and geometric centroid. The reader checks a single closed planar shell, connected coedge rings and opposite uses of every edge before summing signed tetrahedra and first moments. Across all eleven variants these geometric values agree with the licensed solid measurements before and after rebuild.

The eight P03 variants use the same saved-solid integration and match their licensed measurements. The baseline center is `(20, 10, 5) mm`. Reversing the Boss moves it to `(20, 10, -5) mm`. The YZ variant moves it to `(5, 20, 10) mm`.

## Body-free SOLIDWORKS rectangle sketches

The public SOLIDWORKS reader omits the synthetic neutral body when the saved feature and geometry records independently establish a body-free part. This applies to the closed generation-19000 single-rectangle configuration. The native configuration has zero atoms and no region groups. Its resolved feature list contains the typed sketch and ends at the zero footer.

The active configuration's partition must also contain the exact empty part and delta payloads in schema `SCH_3701250_37102_13006`. Both frames must have their known transmit labels, close consecutively with eight zero trailer bytes each, and consume the whole stream. Their complete bodies match the existing empty table vocabulary except for the schema-specific leading word `0x00ef` in both records and the value `0x02` at byte 45 of the delta body. The comparison checks those values without assigning their purpose.

A missing, unsupported or altered partition leaves the existing body fallback in place. A blank partition can also accompany a real feature history, as the [measured pin envelope](../../../../../re/solidworks/records/PinRevolutionEnvelope.md) illustrates. Both proofs are necessary. The body decision applies when B-rep output is disabled. With B-rep output enabled, the reader retains the native partition and delta payloads and keeps returning any typed B-rep as before.

## Verification

The offline public reader returned zero bodies for all six independently measured P01 archives and one body for all eight P03 archives with and without B-rep output. P01 kept one closed four-edge sketch. Its active partition and delta payloads remained available with B-rep enabled. The [licensed readback](../../Workers/SolidWorksQueuedReadback.md) is the source application evidence for both cohorts.

The [archive process regression](../../../../../tests/Research/Archives/SolidWorksBoundaryTests.py) exercises actual public reads against the source cohorts and swaps or corrupts the selected partition in scratch files. It keeps the neutral body when the active geometry contradicts sketch-only history, when an empty partition accompanies the boss, and when the active partition is opaque, truncated, extended or missing. The focused offline public-reader replay completed all 40 reads in Python 3.14.6. The retained observation summary SHA-256 is `34ac50eddc02440557e25997c8fc4e9137eb8c9b562667c4c343520ebc54dabc`.
