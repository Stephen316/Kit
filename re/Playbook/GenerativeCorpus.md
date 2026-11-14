# Phase C — Generative corpus

**Goal:** use the vendor's own API to author a large corpus of documents, from boring ladders to the
strangest shapes, features, assemblies and drawings the application can produce, where every file
comes with a machine-readable record of exactly which parameters, features and values produced it.
That ground truth turns format decoding into a search problem (phase D).

**Inputs:** a licensed vendor install used as an oracle, the API surface for the vendor
([Toolchain.md §3](Toolchain.md#3-vendor-api-surfaces-oracle-and-generator)), the
[shape catalogue](ShapeCatalog.md), and the field hypotheses from phase B.
**Outputs:** thousands of files under `.rescratch/<vendor>/corpus/…`, each with a sidecar manifest,
plus a corpus index committed to `re/<vendor>/corpus/`.

**Boundary:** the generator and every file it makes are research artefacts. They live in `re/` and
`.rescratch/`. Production code never imports the generator, never reads the corpus, and never ships
a byte from it. The corpus teaches rules; the rules ship.

---

## 1. Why generate instead of scavenge

Real-world files vary in fifty ways at once. A file you author varies in exactly the way you chose.
A field that moves when exactly one input moved is located. A field whose value equals a parameter
you set is identified. Real-world corpora remain essential for coverage (they contain values and
combinations your generator never thought of, and they are often localised), but they locate almost
nothing.

The generative corpus has a second job: **it is the held-out test set.** Every rule you derive must
predict files it was not derived from. A big, varied, generated corpus is how you prove a rule
generalises instead of fitting a handful of samples.

---

## 2. Build the oracle loop first

The same loop authors samples and measures output. Build it once, properly.

1. **One fresh process per batch, and per risky candidate.** A malformed file can hard-crash the
   app and poison every later result in that session.
2. **Controls.** Measure a known-good vendor-authored control before and after every batch. If
   either control fails, discard the batch. Without this, a degraded install produces phantom
   findings. The SOLIDWORKS install silently degraded after about 25 crash-inducing launches.
3. **Process hygiene.** Kill orphaned helper and crash-reporter processes between batches. Stacked
   crash handlers were what actually broke the SOLIDWORKS install.
4. **Dialog killer.** A watchdog that enumerates windows and dismisses known modal dialogs
   (`re/tooling/harness/Dismiss.py`). A startup modal blocked COM registration entirely until this
   existed. Log every dialog it dismisses; a dismissed error dialog is a recorded failure, never a
   silent pass.
5. **Absolute paths everywhere.** Relative paths silently returned a null model.
6. **Timeouts.** Every API call that can hang gets a wall-clock limit; a hang is a recorded result.
7. **Serialise access.** Exactly one agent owns the vendor install at a time (see
   [Orchestration.md](Orchestration.md)).
8. **Quantitative measurement.** For each saved sample, ask the app for body count, volume, surface
   area, centre of mass, bounding box, feature tree with types and suppression state, rebuild errors,
   and the value of every parameter. Two independent scalars at least: volume alone cannot see a
   mirrored or flipped body; centre of mass can.

Existing loops to start from: `re/tooling/harness/` (SOLIDWORKS COM), `re/Fusion/LocalOracle/`
(Fusion scripts via the command bridge in
`Documentation/Reference/Research/FusionOracleCommands.md`).

---

## 3. The sample manifest — ground truth for every file

Every generated file gets a sidecar `<name>.manifest.json`. Without it the file is nearly worthless
for phase D. Minimum content:

```json
{
  "schema": "kit-re-corpus-manifest/1",
  "file": "extrude-depth-ladder-0042.SLDPRT",
  "sha256": "…",
  "generator": {
    "script": "re/solidworks/Oracle/GenerateExtrudes.py",
    "git_commit": "…",
    "seed": 1337
  },
  "application": {
    "name": "SOLIDWORKS",
    "version": "2025 SP…",
    "build": "…",
    "locale": "en-US",
    "os": "…"
  },
  "units": { "length": "m", "angle": "rad", "mass": "kg" },
  "family": "extrude-depth-ladder",
  "varied": ["features[1].depth"],
  "api_calls": [
    {
      "call": "ISketchManager.CreateCornerRectangle",
      "args": [0, 0, 0, 0.04, 0.03, 0]
    },
    {
      "call": "IFeatureManager.FeatureExtrusion3",
      "args": ["…every argument, verbatim…"]
    }
  ],
  "model": {
    "features": [
      {
        "index": 0,
        "type": "ProfileFeature",
        "name": "Sketch1",
        "plane": "Front",
        "entities": [{ "kind": "line", "start": [0, 0], "end": [0.04, 0] }],
        "constraints": [{ "kind": "horizontal", "entities": [0] }],
        "dimensions": [{ "name": "D1@Sketch1", "value": 0.04, "driving": true }]
      },
      {
        "index": 1,
        "type": "Extrusion",
        "name": "Boss-Extrude1",
        "end_condition": "blind",
        "depth": 0.0123,
        "reverse": false,
        "draft": null,
        "merge": true
      }
    ],
    "parameters": [
      { "name": "D1@Boss-Extrude1", "expression": "12.3mm", "value": 0.0123 }
    ],
    "equations": []
  },
  "measured": {
    "bodies": 1,
    "volume": 1.476e-5,
    "area": 0.004122,
    "center_of_mass": [0.02, 0.015, 0.00615],
    "bbox": [
      [0, 0, 0],
      [0.04, 0.03, 0.0123]
    ],
    "feature_tree": [
      {
        "name": "Boss-Extrude1",
        "type": "Extrusion",
        "suppressed": false,
        "error": null
      }
    ],
    "rebuild_errors": []
  },
  "controls": {
    "before": { "file": "control.SLDPRT", "ok": true },
    "after": { "file": "control.SLDPRT", "ok": true }
  },
  "exports": {
    "step": "extrude-depth-ladder-0042.step",
    "parasolid_text": "extrude-depth-ladder-0042.x_t"
  },
  "notes": []
}
```

Rules for manifests:

- Record **both** what you asked for (API arguments, in API units) and what the app reports back
  (the feature definition read back through the API after rebuild). They differ more often than you
  expect: the app snaps, clamps, converts units and normalises angles. That difference is itself a
  boundary finding.
- Record values in the API's internal units (SOLIDWORKS: metres and radians; Fusion: centimetres and
  radians) **and** the user-facing expression.
- Record every argument of every call verbatim, including ones you left at defaults.
- Record the read-back feature tree, including names the app assigned.
- Hash the file after saving and closing; some apps write on close.
- Keep the generator script and its git commit; a manifest without a reproducible generator is a
  scavenged file with extra steps.

---

## 4. Corpus design

### 4.1 Families

Organise the corpus into **families**. A family holds everything fixed except a declared set of
varied parameters.

| family type                | what varies                                                           | what it locates                                         |
| -------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------- |
| **Control pair**           | nothing (same script run twice in fresh sessions)                     | noise floor                                             |
| **One-factor ladder**      | one scalar over a range (depth 1 mm … 1 m, logarithmic and linear)    | the field, its encoding and units                       |
| **Boolean pair**           | one flag, both values, in every operation it combines with            | flag bits and the records they add or remove            |
| **Enum sweep**             | one enum through every legal value the API accepts                    | stored enum values, nested records per value            |
| **Count ladder**           | number of features, entities, bodies, instances (1, 2, 3 … n)         | repeated blocks, counts, id allocation, per-item stride |
| **Topology swap**          | same parameters, different profile topology (rect/circle/slot/spline) | profile encoding, entity type tags                      |
| **Reference swap**         | same feature, different reference (plane, face, edge, axis, point)    | reference encoding and resolution                       |
| **Order permutation**      | same features, different creation order or tree reorder               | ordering fields, renumbering, dependency encoding       |
| **Edit history**           | create, then edit, roll back, suppress, delete, undo                  | history/journal state vs current state                  |
| **Pairwise combinatorial** | several factors chosen by an orthogonal array or pairwise design      | interactions between fields at manageable sample counts |
| **Seeded random**          | everything, within legal domains, from a recorded seed                | held-out validation; surprises                          |
| **Boundary set**           | each field at the edges found in phase B                              | clamps, fixups, rejections                              |
| **Version set**            | same model saved in each supported older version                      | version gates                                           |
| **Locale set**             | same model authored on a localised install                            | which strings are localised defaults                    |

### 4.2 Values to choose

Pick values that make the encoding obvious and that stress the loader:

- **Distinctive values** that are easy to find in bytes and impossible to confuse:
  `0.0123456789`, `0.0271828`, `0.0314159`, `0.0424242`, primes in millimetres (`17 mm`, `29 mm`,
  `0.0101 m`). Avoid `0.01`, `0.1`, `1.0`, which collide with everything.
- **Unit tells:** a length of exactly `25.4 mm`, angles of exactly `1 rad` and `57.29577951°`, so you
  can tell metres from millimetres from inches and radians from degrees.
- **Signs and zero:** negative values where legal, exact zero, values just above zero.
- **Magnitude sweeps:** 1e-6 m to 1e3 m on a log scale; the application's own min/max model size.
- **Tolerance edges:** just above and just below the app's linear and angular tolerances.
- **Angle edges:** 0, ε, π/2, π, 2π−ε, 2π, and values beyond 2π if the API accepts them.
- **Long and strange strings:** empty names (if legal), 255+ characters, every script you can type
  (Latin with diacritics, CJK, Arabic RTL, emoji), leading/trailing spaces, characters that are
  special in XML/JSON/paths.

### 4.3 Sizing

- Ladders: 8–32 points each, including both ends of the legal range.
- Enum sweeps: every value.
- Count ladders: at least 1..8 and a few large counts (64, 256, 1000) to find stride and limits.
- Pairwise designs: use a covering array (e.g. via `allpairspy` or a hand-built orthogonal array)
  rather than the full cross product.
- Seeded random: thousands, cheaply, once the loop is stable. Hold 20% out of every analysis.

---

## 5. Generators by vendor

Each generator is a script in `re/<vendor>/Oracle/` (or the existing harness directory) that takes a
family spec and a seed, drives the API, saves the file, reads the model back, measures it, writes the
manifest and closes the document. Outline:

```python
for sample in family.samples(seed):
    doc = app.new_part()
    calls = []
    build(doc, sample, calls)
    doc.rebuild()
    readback = read_model_through_api(doc)
    measured = measure(doc)
    path = save(doc, sample.name)
    close(doc)
    write_manifest(path, sample, calls, readback, measured, controls)
```

### 5.1 SOLIDWORKS

- COM API from Python (`win32com.client.Dispatch("SldWorks.Application")`) or C#.
- Sketches through `ISketchManager` (`CreateLine`, `CreateCircle`, `CreateArc`, `CreateSpline2`,
  `CreateCornerRectangle`), dimensions with `IModelDoc2.AddDimension2`, relations with
  `SketchAddConstraints`.
- Features through `IFeatureManager` (`FeatureExtrusion3`, `FeatureRevolve2`, `FeatureCut4`,
  `FeatureFillet3`, `InsertMirrorFeature2`, `FeatureLinearPattern…`), and read back through
  `IFeature.GetDefinition()` into the matching `*FeatureData` interface.
- Equations via `IEquationMgr`; configurations via `IConfigurationManager`; drawings via
  `DrawingDoc` (`CreateDrawViewFromModelView3`, `InsertModelAnnotations3`).
- Mass properties via `IModelDocExtension.CreateMassProperty`.
- Use the **macro recorder** for every feature you have not scripted before; it emits the exact call
  and argument list.
- API method names carry version suffixes (`…2`, `…3`); use the newest one your install documents
  and record which one you used.

### 5.2 Fusion

- Python scripts executed inside Fusion through the command bridge documented in
  `Documentation/Reference/Research/FusionOracleCommands.md`. The capture scripts in
  `re/Fusion/LocalOracle/Capture*.py` are working templates.
- Build with `adsk.fusion` (`rootComponent.sketches.add`, `sketchCurves.sketchLines.addTwoPointRectangle`,
  `features.extrudeFeatures.createInput`, `ValueInput.createByString("12.3 mm")`,
  `userParameters.add`), export with `exportManager.createFusionArchiveExportOptions`.
- Read back parameters (`design.allParameters`), the timeline (`design.timeline`), bodies
  (`rootComponent.bRepBodies`, volume, bounding box).
- `app.executeTextCommand("PAsset.EntityIds")` and `"PEntity.Properties <id>"` exposed internal entity
  properties in the existing captures. Internal text commands are an extraordinary data-model oracle:
  they show the internal object graph the file serialises. Record which commands you used; they are
  not a stable public API.
- Fusion internal units are centimetres; record both the expression and the internal value.

### 5.3 CATIA V5

- COM Automation (`CATIA.Application`) from Python or VBA.
- `PartDocument.Part`, `Part.ShapeFactory` (`AddNewPad`, `AddNewPocket`, `AddNewShaft`, `AddNewHole`),
  `Part.HybridShapeFactory` for wireframe and surfaces, `Part.Parameters` and `Part.Relations` for
  knowledge, `Part.Update()`.
- Macro recording for unfamiliar features.

### 5.4 NX, Creo, Inventor, Solid Edge, AutoCAD

- **NX:** NXOpen Python journals. Record a journal of each exotic feature, then parameterise.
- **Creo:** J-Link/OTK; trail files and mapkeys for features the toolkit does not expose cleanly.
- **Inventor / Solid Edge:** COM/.NET API; both use CFBF containers, so pair every generator with an
  `olefile` stream census.
- **AutoCAD:** .NET or AutoLISP; script through `accoreconsole` for headless batches. Always also
  `DXFOUT`: the DXF of the same drawing is a labelled text rendering of the same objects.

### 5.5 FreeCAD

Fully open, scriptable, and useful in two ways: as the oracle for `.FCStd`, and as a generator of
neutral reference geometry that another vendor imports (`re/tooling/harness/Author.py`).

---

## 6. Always export siblings

For every generated sample, also save open or text siblings when the app supports them. Each sibling
is an independent labelled view of the same data:

| sibling                        | what it gives you                                                 |
| ------------------------------ | ----------------------------------------------------------------- |
| Parasolid text (`.x_t`)        | the B-rep in readable form; locate the binary Parasolid partition |
| ACIS SAT (text)                | the same for ACIS-based apps                                      |
| STEP AP214/AP242               | geometry and some PMI; OCCT measures it as a second oracle        |
| DXF (for DWG)                  | every object with group codes                                     |
| Older-version save             | version gates                                                     |
| The app's own XML/JSON exports | names and values in readable form                                 |

---

## 7. Go wide: the extreme corpus

Ladders find the common fields. The extreme corpus finds everything else: rare records, nested
objects, enum branches, overflow behaviour, the features real users actually make. Work through the
[shape catalogue](ShapeCatalog.md) tier by tier. For each item:

1. Build it through the API (recorder first if needed).
2. Vary its key parameters as a small ladder.
3. Include it in pairwise combinations with other features.
4. Record failures too: an API call that the app rejects, or a feature that fails to rebuild, is a
   boundary finding. Save the manifest with the error.

Push until the app refuses. The point where it refuses is a boundary worth knowing.

---

## 8. Corpus hygiene

- Store files under `.rescratch/<vendor>/corpus/<family>/` (gitignored); commit the generator, the
  family specs, an index (`re/<vendor>/corpus/Index.json` with file hashes and manifest hashes) and
  small representative samples only when their size is reasonable.
- Never mix Kit-written files into the authored corpus. Mark Kit output with a manifest field
  `"producer": "kit"` and keep it in a separate tree.
- Version the corpus: when the vendor updates, regenerate into a new directory and keep the old.
- Scrub user names and home paths from manifests and captures before committing anything.
- Record which samples are held out. Do not look at held-out samples while deriving a rule.

---

## 9. Exit criteria for phase C

- [ ] Oracle loop with controls, fresh processes, dialog killer and timeouts.
- [ ] Manifest schema in use for every sample, with API arguments, read-back model and measurements.
- [ ] Control pairs, ladders, boolean pairs and enum sweeps for every feature in scope.
- [ ] Count ladders for every repeated structure.
- [ ] Extreme corpus covering the catalogue tiers in scope, including recorded failures.
- [ ] Sibling exports for every sample where supported.
- [ ] Held-out split recorded.
- [ ] Corpus index committed to `re/<vendor>/corpus/`.
