# Capture paired native samples

## Purpose

Use this procedure to make the A02c native captures for the [paired recipes](../../../re/automation/PairSpecs.json).
Each recipe is authored independently in SOLIDWORKS and in Fusion.
Each capture records the native files, the application build and the measured observations.
These captures give later steps an answer key that does not come from a Kit reader.
Use the [step register](AutomationSteps.md) for current status.

A capture is research evidence only.
It does not qualify a reader, a writer or a conversion by itself.

## Rules for every capture

- Author from the recipe only.
  Do not open, convert or copy a Kit-generated file or another capture.
- Use millimetres, the world origin and the planes named in the recipe.
- Give each driving dimension the parameter name from the recipe, for example `width_mm`.
- Record the exact application build, for example `SOLIDWORKS 2025 SP2.0` or the Fusion version string.
- Measure a healthy control document before and after the capture session.
- Record a missing observation as missing.
  Do not substitute an analytic expectation for a measurement.
- Keep every saved file.
  Do not resave a file after you record its hash.

## Files for each capture

Put the files for one application run in one new folder under `re/automation/PairedCaptures/<recipe>/`.

| File                        | Content                                                         |
| --------------------------- | --------------------------------------------------------------- |
| `<recipe>-<app>-baseline-a` | First save of the unchanged baseline                            |
| `<recipe>-<app>-baseline-b` | Second save after a close and fresh reopen                      |
| `<recipe>-<app>-edit-…`     | One save for each independent edit, before the restore          |
| `<recipe>-<app>-units-inch` | The baseline with inch display units and unchanged geometry     |
| `<recipe>-<app>-plane-yz`   | The baseline reauthored on YZ with u = +Y, v = +Z and n = +X    |
| `measurements.json`         | The application build, recipe digest, file hashes and readings |
| `receipt.json`              | The SHA-256 of `measurements.json` and the list of native files |

## P01 — dimensioned rectangular sketch

P01 is a sketch only, with no solid body.
Its split is discovery.

| Item          | Value                                                                  |
| ------------- | ---------------------------------------------------------------------- |
| Plane         | XY (SOLIDWORKS Top plane is XZ; use the Front plane for world XY)      |
| Vertices      | (0, 0), (40, 0), (40, 20), (0, 20) mm                                  |
| Constraints   | Closed loop, two horizontal, two vertical, lower-left vertex on origin |
| Dimensions    | `width_mm` = 40 on the lower edge, `height_mm` = 20 on the left edge   |
| Expected area | 800 mm² (analytic, not a measurement)                                  |
| Edits         | `width_mm` → 41 (820 mm²), `height_mm` → 23 (920 mm²)                  |

SOLIDWORKS default planes are Front = XY, Top = XZ and Right = YZ.
Map planes by basis, not by name.

### SOLIDWORKS checklist

1. Record the exact build from **Help > About SOLIDWORKS**.
2. Open the control part `re/solidworks/examples/.SLDPRT/example.SLDPRT`.
   Record its body count, volume and center of mass from **Evaluate > Mass Properties**.
   Close it without saving.
3. Create a new part.
   Set **Tools > Options > Document Properties > Units** to MMGS.
4. Start a sketch on the **Front** plane.
5. Draw a corner rectangle from the origin to (40, 20).
6. Confirm the four corner coincidences, two horizontal and two vertical relations, and the lower-left corner on the origin.
   Delete any other automatic relations and record that you deleted them.
7. Add a 40 mm dimension on the lower edge.
   Rename it `width_mm` in its **Primary Value** name field.
8. Add a 20 mm dimension on the left edge.
   Rename it `height_mm`.
9. Confirm that the sketch is fully defined.
   Exit the sketch.
10. Record the sketch area with **Evaluate > Measure** or **Section Properties**.
11. Save as `P01-solidworks-baseline-a.SLDPRT`.
12. Close SOLIDWORKS completely, then start it again.
13. Open `baseline-a`.
    Record any load errors or warnings.
    Press **Ctrl+Q** to force a rebuild and record the results again.
14. Save a copy as `P01-solidworks-baseline-b.SLDPRT` with **File > Save As**.
15. Change `width_mm` to 41.
    Rebuild, record the area and save a copy as `P01-solidworks-edit-width_mm-41.SLDPRT`.
16. Change `width_mm` back to 40.
    Rebuild and record the area.
17. Repeat steps 15 and 16 for `height_mm` → 23, saved as `P01-solidworks-edit-height_mm-23.SLDPRT`.
18. Change the document units to IPS.
    Do not change any geometry.
    Save a copy as `P01-solidworks-units-inch.SLDPRT`.
19. Make a new part.
    Repeat steps 3–10 on the **Right** plane.
    Put the corners at world (0, 0, 0), (0, 40, 0), (0, 40, 20) and (0, 0, 20) mm.
    `width_mm` lies along +Y and `height_mm` along +Z.
    In the Right view, +Y is up and +Z points left, so check the corners with **Evaluate > Measure**.
    Save as `P01-solidworks-plane-yz.SLDPRT`.
20. Reopen each saved copy once.
    Record its load errors, warnings and area.
21. Measure the control part again, as in step 2.

### SOLIDWORKS measurement form

Copy this table into a text file next to the saved parts.
Fill in one row for each reading.

| Step | File or state                  | Load errors | Load warnings | Area (mm²) | Fully defined | Relations | Dimensions and values | Notes |
| ---- | ------------------------------ | ----------- | ------------- | ---------- | ------------- | --------- | --------------------- | ----- |
| 2    | Control before                 |             |               |            |               |           |                       |       |
| 10   | Baseline as built              |             |               |            |               |           |                       |       |
| 13   | Baseline-a after reopen        |             |               |            |               |           |                       |       |
| 13   | Baseline-a after rebuild       |             |               |            |               |           |                       |       |
| 15   | `width_mm` = 41                |             |               |            |               |           |                       |       |
| 16   | `width_mm` restored            |             |               |            |               |           |                       |       |
| 17   | `height_mm` = 23               |             |               |            |               |           |                       |       |
| 17   | `height_mm` restored           |             |               |            |               |           |                       |       |
| 18   | Inch display units             |             |               |            |               |           |                       |       |
| 19   | YZ plane baseline              |             |               |            |               |           |                       |       |
| 20   | Each reopened copy (one a row) |             |               |            |               |           |                       |       |
| 21   | Control after                  |             |               |            |               |           |                       |       |

Also record the SOLIDWORKS build, the feature tree names and any suppressed features.
Send the saved parts and the filled form back for `measurements.json` and `receipt.json`.

### Fusion capture

[`GenerateFusion.py`](../../../re/automation/PairedCaptures/P01/GenerateFusion.py) authors P01 through the Fusion API from the recipe.
It does not use a Kit reader, writer or source archive.
Run it from **Utilities > Add-Ins > Scripts and Add-Ins** in Fusion.

The script measures the pinned Fusion control archive before and after the capture.
It then creates and closes only its own documents.
It writes every file in the table above into a new `fusion-<id>` folder.
Each reading records the feature tree, sketch entities, constraints, dimensions, parameters, profile areas and health.
A repeat save follows a document close and archive reopen in the same Fusion process, not an application restart.
The measurements file records that limit.

## Related information

- [Paired recipes](../../../re/automation/PairSpecs.json)
- [Pinned corpus](PinnedCorpus.md)
- [Step register](AutomationSteps.md)
- [CAD success criteria](../Operations/CadSuccessCriteria.md)
