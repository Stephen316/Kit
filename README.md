# Fusion native-file study

This is an experimental, read-only `.f3d` decoder for recovering parametric CAD information. It currently produces JSON. It does not regenerate solid bodies, write native Fusion files, or translate a complete feature history into SolidWorks or FreeCAD.

Work is stored in this standalone Git repository:

```text
/Users/stephenh/.codex/visualizations/2026/10/17/01a14ba1-a51c-7f72-b92e-9f1f0114012e/FusionFileStudy
```

The observed layouts come from locally generated reference files exported by Fusion `2705.1.30`. Coverage is partial and tied to those examples. Each completed stage has a local commit; nothing is pushed remotely.

## Run the reader

Use Python 3 with its standard library. Older Python ZIP implementations need `libzstd` for the archives' compression method 93. On the machine used for this study:

```sh
FUSION_STUDY_ZSTD='/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production/c139e2731e42a0340acc3d34de2cbdb01237a27c/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'
/usr/bin/python3 decode_basics.py --zstd-library "$FUSION_STUDY_ZSTD" profiles-66b0447c28ac/concentric_annulus.f3d > decoded.json
```

Run this from the study directory. Supply a different `libzstd` path if Fusion is installed elsewhere. The flag can be omitted when the Python ZIP implementation supports Zstandard or a system `libzstd` is discoverable. Decoding existing files does not require running Fusion.

The main entry point is `decode_basics.decode_basics(path, zstd_library=None)`. The parameter-only entry point is `decode_parameters.decode_file`. Both read archives without extracting members onto disk.

## What is currently recovered

| Area | Observed support | Main remaining gaps |
| --- | --- | --- |
| Archive and metadata | ZIP/Zstandard members, CRCs, version-8 class registry, primary and inherited object offsets | Other metadata versions; complete field schemas |
| Parameters | Numeric model values, expressions as text, display units, explicit feature-binding references | General expression evaluation and full user-parameter schema |
| Sketch geometry | Points, lines, circles, arcs, ellipses, elliptical arcs, fitted/control/fixed NURBS, conics | Projected geometry and general trimmed/intersection representations |
| Sketch placement | Observed rigid transforms into parent-component coordinates | Assembly occurrence transforms and all placement definitions |
| Constraints | Observed basic geometric constraints and smoothness; internal spline control polygons reported separately | Sketch patterns, offsets, surface constraints and a general solver |
| Dimensions | Linear orientations, offset, radius, diameter, angle, ellipse radii, concentric spacing, tangent distance, linear diameter | Tangent-side choices; driving state outside the observed shared linear class |
| Profile selection | Sketch curve tags, loop membership, outer/inner flags for observed profiles | General trimming and loop traversal order |
| Extrusion | Join/cut/intersect/new body; one/two-sided and symmetric extents; profile/offset/entity starts; distance/to-entity/through-all ends; taper | Full input topology, all combinations and end-condition variants |
| Revolve | Observed new-body angle/full-turn data and native origin-axis selection | General operations, multiple extents and arbitrary axis definitions |
| Construction geometry | Offset/angle plane geometry, custom axis/point names and geometry | Complete parametric support-entity definitions |
| Other modeling tools | Partial sweep, loft, circular pattern, combine, draft, free-move and thicken settings | Complete input body/face/edge references and reconstruction |
| Dress-up/body tools | Fillet, chamfer, shell, hole, rectangular pattern, mirror and scale names and numeric parameters; split-body record/name | Feature-specific modes and complete topology selection |
| Unknown features | Observed feature-class ancestry exposes unsupported feature records explicitly | Unknown ancestry and unimplemented native fields |
| Timeline and state | Explicit ordered feature references, groups and collapse state, suppression and rollback flags; visible indices and derived marker position in observed root-component cases | General assembly/component history composition and other group/state layouts |

Internal lengths use centimetres and angles use radians in the recovered numeric records. Display units such as `mm` are separate. Sweep path fractions are unitless. Sketch-local geometry remains available alongside decoded component-coordinate values.

The feature `stored_index` is an internal native field. It is **not a global timeline position**. Record-offset order also must not be used as modeling history: a controlled reorder changed the explicit history list while leaving record order unchanged.

Use `timeline_decoding.sequences` for observed history order. `feature_order` excludes group markers; `visible_entries` reflects decoded group expansion. Marker position is derived from rollback flags and group projection. Multiple history owners remain separate. Missing or unrecognized records are reported rather than assigned a guessed order.

## Evidence and navigation

- `fusion-class-catalog.json` catalogs opaque class GUIDs, namespaces, base classes, and meanings observed across the local corpus. Type numbers vary between files; they are not universal feature IDs.
- `*-decoding.json` files are stage-specific evidence snapshots with focused comparisons. Historical snapshots can describe an item as unsupported that a later stage implements. Run the reader for current output.
- Generated sample folders contain `.f3d` archives and `ground_truth.json` captured through Fusion's API. Generator scripts use new documents, export locally, and close only their own documents without saving to the cloud.
- Generator scripts require execution inside Fusion's Python environment. They are not ordinary terminal scripts. Existing archives are sufficient to use the decoder.

The metadata index validates object/header identities, registered primary classes, and continuation inheritance. Field meanings are still inferred from a limited corpus; a validated record boundary does not prove that every field in the record is understood.

## Continue the research

The active request is to keep expanding coverage until the user stops the work. Completed stages must be committed locally with focused checks. Do not push, overwrite unrelated project work, or describe partial decoding as complete translation.

Useful next areas are component/assembly ownership and transforms; broader timeline composition; remaining sketch patterns and offsets; feature-specific selections and modes; and BRep topology. A native writer, full geometry regeneration, and integration with the Kit translation pipeline remain separate unfinished work.

Use small controlled API examples, vary one setting where practical, and retain unknown fields. Prefer metadata/class identities and explicit references over byte searches or inference from geometry alone.
