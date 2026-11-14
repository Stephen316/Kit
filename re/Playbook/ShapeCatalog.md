# Shape catalogue — what to generate

The generative corpus must cover far more than rectangles and pads. Real users make lofts with guide
curves, variable fillets, patterns of patterns driven by equations, and drawings with GD&T on every
edge. Each of those is a record type, a nested object or an enum branch you will never see unless you
generate it.

Work tier by tier. Each tier assumes the previous one's fields are located. For every item, build a
small ladder over its key parameters and include it in pairwise combinations (see
[GenerativeCorpus.md §4](GenerativeCorpus.md#4-corpus-design)). Record API rejections and rebuild
failures as boundary findings.

Names below are generic; map each to the vendor's feature name and API call, and record that mapping
in `re/<vendor>/corpus/`.

---

## Tier 0 — calibration

| item                                   | why                                     |
| -------------------------------------- | --------------------------------------- |
| empty part, saved twice                | the minimal file; noise floor           |
| empty part with renamed default planes | where names live; localisation tells    |
| one sketch point at the origin         | the smallest sketch record              |
| one line, one circle, one arc          | entity tags and their geometry encoding |
| one rectangle extruded, depth ladder   | the first feature field; units          |
| same, on each default plane            | plane references and placement frames   |
| same, both directions and reversed     | direction flags                         |
| unit-system variants (mm, m, inch)     | document units vs stored units          |

## Tier 1 — the core parametric set

**Sketch geometry:** lines, centre-point and three-point arcs, tangent arcs, circles, ellipses and
elliptical arcs, parabolas and conics where available, polygons, slots, fillets and chamfers in
sketch, construction geometry, points, centrelines.

**Sketch constraints:** coincident, horizontal, vertical, parallel, perpendicular, tangent, equal,
concentric, symmetric, midpoint, fixed, collinear, curvature-continuous, pierce. Over-, under- and
fully-defined sketches. Driven (reference) dimensions vs driving dimensions.

**Dimensions:** linear, aligned, angular, radial, diameter, arc length, ordinate. Each with a
distinctive value, a tolerance, and an expression referencing a parameter.

**Features:** extrude (blind, through all, up to next, up to vertex, up to surface, offset from
surface, mid-plane, up to body), cut-extrude with the same end conditions, revolve (one-direction,
two-direction, mid-plane, full revolution), cut-revolve, simple and countersunk/counterbored holes,
fillets (constant radius), chamfers (distance-distance, distance-angle), shell, draft, rib, mirror,
linear and circular patterns.

**Parameters:** user parameters, global variables, equations linking dimensions, units in
expressions, a parameter used by several features.

## Tier 2 — the hard parametric set

- **Splines:** through-point and control-point splines with 2, 3, 10, 100, 1000 points; closed
  periodic splines; splines with tangency and curvature handles set; degree variations.
- **3D sketches** and **curves:** helices (constant pitch, variable pitch, tapered), spirals,
  projected and intersection curves, composite curves, curves through XYZ points imported from a
  file, equation-driven curves.
- **Sweeps:** along open and closed paths, with twist (constant and along path), with guide curves,
  with orientation options, thin-feature sweeps, solid-profile (tool body) sweeps.
- **Lofts:** 2, 3, 10 profiles; with guide curves; with centreline; start/end tangency and
  curvature conditions; closed loft; lofts to a point; profiles with different segment counts.
- **Boundary features** and **surface fills** with continuity conditions.
- **Variable-radius fillets**, face fillets, full-round fillets, setback fillets, fillets with
  hold lines and conic sections; fillets that consume entire faces.
- **Draft** with neutral plane, parting line and step draft.
- **Shell** with different thicknesses per face, outward shell.
- **Patterns:** sketch-driven, curve-driven, table-driven, fill patterns, variable patterns,
  patterns of patterns, patterns that skip instances, patterns whose count is an equation.
- **Mirror** of bodies and of features, across planes and faces.
- **Multi-body parts:** new-body operations, combine (add, subtract, common), split, move/copy body,
  delete body, bodies that touch, bodies that are disjoint, zero-thickness failures.
- **Reference geometry:** offset, angled, three-point, normal-to-curve, mid-plane, tangent planes;
  axes, points and coordinate systems built in each way the app allows.
- **Configurations / design tables / variants:** several configurations with suppressed features,
  overridden dimensions, different materials; a design table driving 50 variants.
- **Thin features:** thin extrudes, thin revolves, thin sweeps.
- **Hole wizard / standard holes:** every standard and type the app offers, tapped, with cosmetic
  threads.
- **Cosmetic features:** threads, decals, appearances on faces vs bodies vs features.

## Tier 3 — surfaces, freeform and direct modelling

- Surface extrude, revolve, sweep, loft, offset, knit, trim, untrim, extend, ruled, planar, fill,
  thicken, replace face, delete face, and surface-to-solid conversion.
- Freeform/sub-division modelling (T-splines in Fusion, Freeform in SOLIDWORKS, Imagine & Shape in
  CATIA, Freeform in Creo): boxes, cylinders and tori with creases, symmetry, edits, conversion to
  B-rep. `re/Fusion/LocalOracle/CaptureTSpline.py` is an existing starting point.
- Direct edits on history-based parts: move face, offset face, delete and heal, push/pull.
- Imported dumb solids (STEP in) followed by parametric features on top: the import record, then
  history built on non-parametric geometry.
- Mesh bodies and mesh-to-B-rep conversions; graphics-only bodies.

## Tier 4 — domain features

- **Sheet metal:** base flange, edge flange, miter flange, hem, jog, sketched bend, lofted bend,
  forming tools, unfold/fold, flat pattern, K-factor and bend tables, gauge tables.
- **Weldments / frames:** structural members with profiles, trim/extend, end caps, gussets, cut lists.
- **Mould tools:** parting lines, parting surfaces, core/cavity, shut-offs.
- **Plastic features:** lip/groove, mounting boss, snap hook, vent.
- **Threads and fasteners:** modelled threads, toolbox/content-centre parts.
- **Routing and wiring** where the product has it.
- **Generative and simulation-derived geometry** where it is stored in the part.

## Tier 5 — assemblies

- Components inserted at the origin, at arbitrary transforms, rotated by awkward angles
  (1 rad, 179.999°), mirrored, scaled where allowed.
- Every mate or joint type: coincident, parallel, perpendicular, tangent, concentric, distance,
  angle, lock, gear, rack and pinion, cam, slot, hinge, screw, universal, width, path, limit mates;
  Fusion rigid/revolute/slider/cylindrical/pin-slot/planar/ball joints and motion links.
- Flexible vs rigid subassemblies; nested subassemblies five deep.
- Component patterns (linear, circular, feature-driven), mirror components.
- Assembly-level features (cuts through several components, assembly fillets where supported).
- In-context parts with external references; broken external references.
- Configurations of assemblies, suppressed and lightweight components, virtual/internal components.
- Assemblies referencing parts by relative path, absolute path, and moved paths.
- Large counts: 1, 10, 100, 1000 instances of the same part.

## Tier 6 — drawings

- Sheets of every standard size and orientation; custom sheet sizes; several sheets.
- Sheet formats and title blocks with linked properties.
- Views: standard three-view, isometric, auxiliary, section (full, half, aligned, offset),
  detail views with different scales, broken views, broken-out sections, crop views, alternate
  position views, exploded views, flat-pattern views.
- View scales including odd ones (1:3.7, 17:1); views rotated by arbitrary angles.
- Dimensions of every kind on views; model dimensions vs reference dimensions; ordinate and
  baseline sets; chain dimensions; dimensions with tolerances (bilateral, limit, fit), precision
  overrides, dual units, text overrides.
- Annotations: notes with formatting and fields, balloons and stacked balloons, surface finish
  symbols, weld symbols, datum features and targets, GD&T feature control frames with every
  characteristic and modifier, centre marks, centrelines, cosmetic threads, hatches with patterns
  and angles, blocks.
- Tables: BOM (top-level, parts only, indented), revision tables, hole tables, bend tables,
  general tables, weld tables.
- Layers, line styles, line weights, colours, fonts, text heights.
- Drawings of a model that has since changed (stale views) and drawings whose model is missing.

## Tier 7 — pathological and boundary

Push the application until it refuses, and record where.

- Smallest and largest geometry the app allows; geometry at the tolerance limit.
- A feature tree with 1000+ features; a sketch with 10 000 entities; a pattern with 10 000 instances.
- Deep dependency chains (each feature references the previous one's face).
- Features that fail to rebuild (dangling references, impossible fillets) saved in the failed state.
- Suppressed, rolled-back and frozen features; rollback bar in the middle of the tree.
- Features renamed to empty, to 255+ characters, to every Unicode script, to names that look like
  other features' internal ids.
- Self-intersecting sketches, zero-length entities, coincident duplicate entities.
- Equations with circular references (as far as the app allows), with functions (`sin`, `if`,
  `iif`), with units that cancel.
- Bodies with thousands of faces (knurls, text embossed in many fonts, lattices).
- Files saved from very old versions and opened/saved in new ones.
- Files saved with every option the save dialog offers (previews off/on, geometry cache off/on,
  "save as copy", "pack and go").
- Parts with custom properties of every type (text, date, number, yes/no, linked equations).
- Materials and appearances from every library, including custom ones.

---

## Recording what each item located

When an item's ladder produces a confirmed field, note the item in the field's evidence row. When an
item produces a record type nobody has decoded, add it to the vendor's open-questions list. The
catalogue is complete for a vendor when every item in scope has either located its fields or has a
recorded unknown with the evidence needed to close it.
