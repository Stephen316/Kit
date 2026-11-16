# Capture paired native samples

## Purpose

Use this procedure to make the A02c native captures for the [paired recipes](../../../re/automation/PairSpecs.json).
Each recipe is authored independently in SOLIDWORKS and in Fusion.
Each capture records the native files, the application build and the measured observations.
These captures give later steps an answer key that does not come from a Kit reader.
Use the [step register](AutomationSteps.md) for current status.
The UI steps below specify the authoring operations for the harnesses and workers. Use the [SOLIDWORKS COM harness](SolidWorksCaptureAuthoring.md) or [Fusion capture queue](#fusion-captures) for scripted runs. Use the [Fusion fresh-process procedure](../../Changes/Research/FusionReadback/FusionFreshProcessEvidence.md) for separate restart evidence.
Use the [standalone SOLIDWORKS P02 readback](../../Changes/Research/Workers/SolidWorks/CircleBindingReadback.md) to verify the saved circle dimension binding in a fresh licensed session.
The A08c workers own dispatch and native application recovery. A08e supplies the Windows supervisor support needed to run both applications on one host.
The supplemental SOLIDWORKS through-all control uses a standalone collector on an isolated licensed Windows host. Its failure receipt records cleanup of the exact launched process. [Scope collector startup cleanup](../../Changes/Research/Workers/SolidWorks/ScopeStartupCleanup.md)
For a hard cutoff across synchronous COM calls, run the standalone collector in its dedicated Windows Job Object. [Scope campaign watchdog](../../Changes/Research/Workers/SolidWorks/ScopeWatchdog.md)
The scope collector records the direct or definition-edit authoring route for each explicit Cut and rechecks the intended policy through fresh reopen and rebuild. [Explicit Cut retry](../../Changes/Research/Workers/SolidWorks/ScopeExplicitFallback.md)

A capture is research evidence only.
It does not qualify a reader, a writer or a conversion by itself.

## Preflight supplemental readbacks

Use the [sealed supplemental-evidence preflight](../../Changes/Research/Controller/PairedEvidenceManifest.md) before handing private readbacks to the admission owner.
Its manifest binds both application lanes, requested P01–P04 recipes, source revisions, specifications and normalized report digests.
The public SOLIDWORKS lanes replay their original raw receipt chains before comparing report digests and native archive identities.
Normalized JSON alone is insufficient.
Missing Fusion or original P04 verifier handoffs remain explicit dependencies.
The command preserves original captures and frozen rules, evaluates no qualification, and returns exit code `2` while admission is blocked.
Keep P05 reserved for its independent holdout evaluation.

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
P05 has no YZ file because its recipe fixes the XZ profile plane and the world Z axis.

| File                                | Content                                                         |
| ----------------------------------- | --------------------------------------------------------------- |
| `<recipe>-<app>-baseline-a`         | First save of the unchanged baseline                            |
| `<recipe>-<app>-baseline-b`         | Second save after a close and fresh reopen                      |
| `<recipe>-<app>-edit-…`             | One save for each independent edit, before the restore          |
| `<recipe>-<app>-units-inch`         | The baseline with inch display units and unchanged geometry     |
| `<recipe>-<app>-plane-yz`           | The baseline reauthored on YZ with u = +Y, v = +Z and n = +X    |
| `P03-<app>-direction-negative`      | P03 with the boss reversed to −Z and the same depth             |
| `P04-<app>-termination-through-all` | P04 with the cut reauthored as through-all                      |
| `measurements.json`                 | The application build, recipe digest, file hashes and readings  |
| `receipt.json`                      | The SHA-256 of `measurements.json` and the list of native files |

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

## Shared SOLIDWORKS steps

Use these steps in every recipe below.

- **Control and setup:** do P01 steps 1–3 before you start, and P01 step 21 at the end.
- **Repeat save:** after the baseline, do P01 steps 11–14 with that recipe's file names.
- **Edits:** change one driving dimension at a time.
  Rebuild, record the readings and save a copy as `<recipe>-solidworks-edit-<name>-<value>.SLDPRT`.
  Change the value back, rebuild and record the readings again before the next edit.
- **Inch units:** do P01 step 18 on the restored baseline.
- **Reopen:** reopen each saved copy once and record its load errors, warnings and readings.

For a solid, record the body count, volume and center of mass from **Evaluate > Mass Properties** with MMGS units.
Use the measurement form from P01 and add volume and center-of-mass columns.

## P02 — dimensioned circular sketch

P02 is a sketch only.
Its split is qualification.

| Item          | Value                                                   |
| ------------- | ------------------------------------------------------- |
| Plane         | XY (SOLIDWORKS Front plane)                             |
| Geometry      | Circle with its center on the origin                    |
| Dimension     | `diameter_mm` = 10, a diameter dimension, not a radius  |
| Expected area | 25π ≈ 78.539816 mm² (analytic, not a measurement)       |
| Edits         | `diameter_mm` → 16 (64π ≈ 201.061930 mm²)               |
| Variants      | Inch units, and the same circle on the Right plane (YZ) |

1. Sketch a circle on the Front plane with its center on the origin.
2. Add a **diameter** dimension of 10 mm and rename it `diameter_mm`.
3. Confirm that the sketch is fully defined and record its area.
4. Save as `P02-solidworks-baseline-a.SLDPRT`, then follow the shared steps.
5. For the YZ variant, make a new part and repeat steps 1–3 on the Right plane.
   Save as `P02-solidworks-plane-yz.SLDPRT`.

## P03 — one-sided blind boss

P03 is the P01 rectangle extruded into a block.
Its split is discovery.

| Item           | Value                                                                 |
| -------------- | --------------------------------------------------------------------- |
| Sketch         | The P01 rectangle on the Front plane, with `width_mm` and `height_mm` |
| Feature        | **Boss-Extrude**, blind, one direction, +Z, no draft, new body        |
| Depth          | `depth_mm` = 10                                                       |
| Expected solid | 1 body, 8000 mm³, center of mass (20, 10, 5) mm (analytic)            |
| Edits          | `width_mm` → 41, `height_mm` → 23, `depth_mm` → 12                    |
| Variants       | Inch units, YZ plane, and the boss reversed to −Z with depth 10       |

1. Make the P01 rectangle (P01 steps 3–9).
2. Add a blind **Boss-Extrude** of 10 mm toward +Z.
   Rename its depth dimension `depth_mm`.
3. Record the body count, volume and center of mass.
4. Save as `P03-solidworks-baseline-a.SLDPRT`, then follow the shared steps.
5. For the YZ variant, make a new part on the Right plane with the corners from P01 step 19.
   Extrude 10 mm toward +X and save as `P03-solidworks-plane-yz.SLDPRT`.
6. For the direction variant, make a new part like steps 1–2, but use **Reverse Direction** so the block goes from z = 0 to z = −10.
   Save as `P03-solidworks-direction-negative.SLDPRT`.

## P04 — blind cut in a parent block

P04 adds a rectangular pocket to the top face of the P03 block.
Its split is discovery.

| Item           | Value                                                                                                             |
| -------------- | ----------------------------------------------------------------------------------------------------------------- |
| Parent         | The P03 block, 40 × 20 × 10 mm                                                                                    |
| Cut sketch     | On the top face (z = 10), 10 × 8 mm rectangle centered at (20, 10)                                                |
| Center binding | Center u = `width_mm / 2`, center v = `height_mm / 2`, through equations                                          |
| Dimensions     | `cut_width_mm` = 10, `cut_height_mm` = 8                                                                          |
| Feature        | **Cut-Extrude**, blind, `cut_depth_mm` = 4, into the block (−Z)                                                   |
| Expected solid | 1 body, 7680 mm³, center of mass (20, 10, 4.875) mm (analytic)                                                    |
| Edits          | `width_mm` → 44, `height_mm` → 24, `depth_mm` → 12, `cut_width_mm` → 12, `cut_height_mm` → 10, `cut_depth_mm` → 5 |
| Variants       | Inch units, YZ plane, and the cut reauthored as **Through All**                                                   |

1. Make the P03 block (P03 steps 1–2).
2. Start a sketch on the **top face** of the block, not on a new plane.
3. Draw a 10 × 8 mm rectangle near the middle of the face.
   Add a construction diagonal and a point at its midpoint.
4. Dimension the rectangle `cut_width_mm` = 10 and `cut_height_mm` = 8.
5. Dimension the midpoint from the origin horizontally and vertically.
   Set those values to the equations `= "width_mm@RectangleSketch" / 2` and `= "height_mm@RectangleSketch" / 2`, or the names your sketch uses.
6. Add a blind **Cut-Extrude** of 4 mm into the block.
   Rename its depth `cut_depth_mm`.
7. Record the readings and save as `P04-solidworks-baseline-a.SLDPRT`, then follow the shared steps.
8. For the YZ variant, build steps 1–6 from the P03 YZ variant and save as `P04-solidworks-plane-yz.SLDPRT`.
9. For the termination variant, build steps 1–5, then use **Through All** for the cut.
   Save as `P04-solidworks-termination-through-all.SLDPRT`.

## P05 — full annular revolution

P05 revolves a rectangle around the world Z axis into a ring.
Its split is holdout.

| Item           | Value                                                                            |
| -------------- | -------------------------------------------------------------------------------- |
| Plane          | XZ (SOLIDWORKS Top plane), with u = +X and v = +Z                                |
| Profile        | Corners (2, 0), (6, 0), (6, 12), (2, 12) mm in (x, z), lower edge on z = 0       |
| Axis           | World Z through the origin, bound explicitly (use the Z axis, not a sketch line) |
| Dimensions     | `inner_radius_mm` = 2 and `outer_radius_mm` = 6 from the axis, `height_mm` = 12  |
| Feature        | **Revolve**, one direction, `angle_deg` = 360, new body                          |
| Expected solid | 1 body, 384π ≈ 1206.371579 mm³, center of mass (0, 0, 6) mm (analytic)           |
| Edits          | `inner_radius_mm` → 3, `outer_radius_mm` → 7, `height_mm` → 14, `angle_deg` → 90 |
| Variants       | Inch units only                                                                  |

1. Show the temporary axes with **View > Hide/Show > Temporary Axes**.
2. Sketch the profile rectangle on the **Top** plane at the corners above.
   In SOLIDWORKS, the Top plane is XZ, so check the corner positions with **Evaluate > Measure**.
3. Put the lower edge on the origin's x line, so it lies on z = 0.
4. Dimension the inner and outer edges from the origin as `inner_radius_mm` and `outer_radius_mm`, and the side as `height_mm`.
5. Add a **Revolve** about the world Z axis, one direction, 360°.
   Rename the angle `angle_deg`.
6. Record the readings and save as `P05-solidworks-baseline-a.SLDPRT`, then follow the shared steps.
7. For the 90° edit, record which way the ring sweeps.
   The recipe sweep starts at +X and turns toward +Y.

## Fusion captures

Each recipe folder has a `GenerateFusion.py` that authors the recipe through the Fusion API.
P01 has its own complete script.
P02–P05 call the shared [`FusionCapture.py`](../../../re/automation/PairedCaptures/FusionCapture.py).
The scripts do not use a Kit reader, writer or source archive.

Run a script in one of two ways:

- Open **File > View > Show Text Commands** in Fusion, select **Txt** and enter `Python.RunScript "<absolute path to GenerateFusion.py>"`.
- Start the [`KitCaptureRunner`](../../../re/automation/PairedCaptures/Runner/KitCaptureRunner/KitCaptureRunner.py) add-in from **Utilities > Add-Ins > Scripts and Add-Ins**.

The runner add-in works on Windows and macOS.

| Item          | Windows                                              | macOS                                                                    |
| ------------- | ---------------------------------------------------- | ------------------------------------------------------------------------ |
| Add-in folder | `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\` | `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/` |
| Runner folder | `%APPDATA%\KitCaptureRunner\`                        | `~/Library/Application Support/KitCaptureRunner/`                        |

Copy the `KitCaptureRunner` folder into the add-in folder.
Write `config.json` in the runner folder with `allowed_root` set to the absolute `re/automation/PairedCaptures` path.
Queue a job by writing a JSON file such as `{"script": "<absolute path to GenerateFusion.py>"}` into `queue/`.
The runner takes jobs in name order, one at a time, and starts the next job as soon as the last one finishes.
It runs only `GenerateFusion.py` files inside the configured folder.
It writes `<job>.done` for each job and keeps `runner.json` current with the job count, failures, busy time and utilization.
It does not start automatically.

Each script measures the pinned Fusion control archive before and after the capture.
It creates and closes only its own documents.
It writes every file for its recipe into a new `fusion-<id>` folder.
Each reading records the feature tree, sketch curves, constraints, dimensions, parameters, profile areas, bodies and health.
P01 records sketch entity coordinates in sketch space with the sketch frame.
P02–P05 record curve endpoints in world coordinates.
Analytic comparisons are labelled separately and never replace a measurement.
A repeat save follows a document close and archive reopen in the same Fusion process, not an application restart.
The measurements file records that limit.

## Related information

- [Paired recipes](../../../re/automation/PairSpecs.json)
- [Pinned corpus](PinnedCorpus.md)
- [Step register](AutomationSteps.md)
- [CAD success criteria](../Operations/CadSuccessCriteria.md)
