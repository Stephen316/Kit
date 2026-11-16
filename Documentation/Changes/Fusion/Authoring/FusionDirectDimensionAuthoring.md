# Explicit direct-owned Fusion dimension authoring

## Behavior

The positive-XY Boss research generator now composes the real authoring stages directly.
It creates the author state, root collections, sketch, extrusion, geometry, material and packed document through the existing emitters.
Its sketch allocation order is four axis constraints, the distinct Origin-to-corner coincidence, two annotated dimensions, then their parameter and dependency links.
It no longer replaces shared build functions or changes the profile kind temporarily.

`AddCollectMut(Author, DirectOwned=True)` omits the global length parameter and its name-table subject.
The caller supplies the complete directly owned parameter table before emission.
The default `DirectOwned=False` preserves ordinary authoring behavior.
This internal allocation option does not admit new portable documents at the public writer boundary.

The research Boss keeps exactly four literal parameters: sketch-owned `width_mm` and `height_mm` in slots 1 and 2, followed by Boss-owned `depth_mm` and zero taper `d4` in slots 3 and 4.
The existing name index, annotation values and operands, Origin identity, selected profile, compute graph, material and body emitters remain independently checked by the source-derived probe.
The historical P01 Origin probe reuses the extracted coincidence helper at its original point in the existing sequence.

## Usage

Use Python 3.14 with the locked project dependencies and the pinned discovery objects available locally.
The existing command accepts a new private directory outside the checkout:

```sh
PYTHONPATH=src:re/automation uv run --frozen --python 3.14 python -B \
  re/Fusion/Reconstruction/DimensionAuthoring/SourceBossProbe.py \
  --output /private/P03Candidates
```

It generates and independently checks the four measured positive-XY P03 discovery cases before publishing the archives and their sealed manifest.
The [existing Boss note](../../Research/Readers/Comparison/FusionSourceBossProbe.md) describes the source bindings and candidate checks.

## Evidence and limitations

The [released feasibility pilot](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6926364607) reported a real-stage in-memory 37 × 21 × 11 mm candidate and all four measured positive-XY controls.
It checked literal driver roles, distinct Origin and corner, reciprocal operands, profile identity, volume and centroid.
The [public source handoff](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6926463528) identifies reachable source `2817a2e90c2ffcf107cad3340021f4a037d12981` and states that the pilot produced no new source artifact.
Those are reported offline feasibility observations, not execution evidence for this change revision.

New process coverage invokes the existing source-derived Boss CLI through allocation, geometry, material, packing and saved-record validation.
It checks the four literal parameter inventories, archive seals and prism results.
A second process invokes the historical Origin CLI and checks its sketch-only result and fourteen pinned control comparisons.
Pinned formatting, type, steering, path, rationale, binary-range and whitespace checks validate this change statically.
No generator, comparison, tests, collection or CAD process ran locally.
Hosted process execution remains required.

This change does not qualify a pair, establish native application acceptance, change the default writer, alter its native-semantic guards or close A11.
The source-derived P03 candidates still require licensed driving edits, restoration, rebuild and fresh-process reopen with healthy controls.
Physical density and mass parity retain their separate evidence requirements.
