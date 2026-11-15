# Fusion P04 saved cut selection routes

The P04 archive report adds `selection_routes` for the eleven Fusion discovery exports from build `2706.1.17`. Run it with Python 3.14 or later to read the exact bytes pinned at `89c25945f5833ad9c3a1c6c683df510b5702dd54`. The paired intake checks the discovery split, archive roster, recipe, receipt and measurement digests before reading the saved models. [Extent and source evidence](FusionCutExtentEvidence.md)

```powershell
python -B re/automation/FusionCutExtentEvidence.py > FusionCutExtentEvidence.json
```

The command was run with Python 3.14.6. All eleven archives, including the width and height edits, YZ basis and inch display, establish these indexed routes.

| Observed route | Archive-local records |
| --- | --- |
| Cut body-list entry, repeated in the feature dependencies | Cut `446` → proxy `447` → body descriptor `450` → anchor `315` → Body `309` |
| Cut profile and sketch-data body reference | Profile proxy `454` → profile descriptor `457` → sketch data `330`, with reciprocal sketch feature `334` and a direct body reference to `309` |
| Cut sketch's separately owned face selection | Sketch feature `334` → proxy `347` → face descriptor `350` → bounded-face recipe `353` and anchor `315` |
| Body provenance | Anchor `315` and `BlindBoss` feature `277` reference each other, and the owned descriptor support records independently reference `277` |
| Through-all first-side end field, unique to the through-all variant | Proxy `461` → body descriptor `464` → the same anchor `315` |

The JSON retains class, byte range and SHA-256 for each reported record. The command requires matching owner and repeated dependency references, typed contexts and historical body anchors, and a reciprocal support record for each descriptor. The supported descriptor trailers carry marker bytes `04 01 00 00` at both marker positions where the general research selection readers expect `01 01 00 00`. The route check is scoped to these exact P04 exports. [Evidence command](../../../../re/automation/FusionCutExtentEvidence.py)

The generator originally selected the planar boss top and let Fusion determine the participating bodies. The saved file proves an owned face recipe and a common historical body across the sketch and cut routes. Exact BRep face resolution, API participant-body meaning, the through-all end-field behavior and multi-body discrimination still require separate evidence. Native restart readback and full constraint or dimension bindings remain open. Main's authored-Fusion acceptance used different cylinder documents and observed an edit without a newly persisted revision. It supplies no P04 native comparison.
