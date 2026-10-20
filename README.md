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
| ASM body/history blobs | Observed `ASM BinaryFile8` tokens and partial body/lump/shell/face/loop/coedge/edge/vertex graphs; points, straight/elliptical curves and planes with parameter bounds | Persistent final-body mapping, historical variants, transforms, other surfaces, trims and complete topology |
| Body/blob bindings | Explicit native body IDs, opaque handles, stored tags and history-blob filename; conditional ordered leading-root candidates | General root association, user-visible names, component ownership and historical/final state selection |
| Parameters | Numeric model values, expressions as text, display units, explicit feature-binding references | General expression evaluation and full user-parameter schema |
| Sketch geometry | Points, lines, circles, arcs, ellipses, elliptical arcs, fitted/control/fixed NURBS, conics | Projected geometry and general trimmed/intersection representations |
| Sketch placement | Observed rigid transforms into parent-component coordinates and composed world coordinates through decoded occurrence paths | Other placement definitions and unresolved instance contexts |
| Constraints | Observed basic constraints, smoothness, signed offset parent/child pairs, and single-circle rectangular/circular sketch patterns; internal spline control polygons reported separately | General pattern inputs, suppression, arbitrary axes, topology-changing offsets, surface constraints and a solver |
| Dimensions | Linear orientations, offset, radius, diameter, angle, ellipse radii, concentric spacing, tangent distance, linear diameter | Tangent-side choices; driving state outside the observed shared linear class |
| Profile selection | Sketch curve tags, loop membership, outer/inner flags for observed profiles | General trimming and loop traversal order |
| Extrusion | Join/cut/intersect/new body; one/two-sided and symmetric extents; profile/offset/entity starts; distance/to-entity/through-all ends; taper | Full input topology, all combinations and end-condition variants |
| Revolve | Observed join/cut/intersect/new body, signed one-sided/symmetric/two-sided angles, one/two construction-plane entity extents, solid/surface and projected-axis flags; native origin axes | Other target entities, direction hints, arbitrary axes and geometry regeneration |
| Construction geometry | Offset/angle plane geometry, custom axis/point names and geometry | Complete parametric support-entity definitions |
| Other modeling tools | Partial sweep, loft, circular pattern, combine, draft, free-move and thicken settings | Complete input body/face/edge references and reconstruction |
| Holes | Observed simple/counterbore/countersink settings, distance/through-all/to-entity ends; default/reversed direction, point/sketch-point/multiple-point/center-edge placement coordinates and references | Threads, full point/edge association definitions, supporting/target faces and other position modes |
| Scale, mirror and shell | Uniform/nonuniform scale factors and observed origin-point selection; mirror native origin planes, combine state and stitch tolerance; shell inside/outside thicknesses, sharp/rounded type and tangent-chain state | Selected bodies/faces, arbitrary scale points/planes and mirror compute options |
| Rectangular patterns | Observed quantities/distances, spacing versus extent, separate symmetry flags and explicit native origin-axis selections | Input entities, compute options, suppressed instances and arbitrary direction entities |
| Fillets and chamfers | Ordered edge-set definitions, explicit numeric bindings, tangent/curvature flags; constant/chord/asymmetric/endpoint-variable fillets, corner mode; equal/two-distance/distance-angle chamfers and observed flip flags | Actual edges/faces, asymmetric flip state, intermediate radii, rule/full-round fillets and other layouts |
| Split bodies | Observed tool-extension flag, target counts/descriptors and explicit origin/custom construction-plane tool references | Target body topology, nonplanar tools and resulting split solids |
| Unknown features | Observed feature-class ancestry exposes unsupported feature records explicitly | Unknown ancestry and unimplemented native fields |
| Timeline and state | Explicit ordered feature references, groups and collapse state, suppression and rollback flags; visible indices and derived marker position in observed root-component cases | General assembly/component history composition and other group/state layouts |
| Local assemblies | Component definitions, repeated/native occurrences, parent collections, nested rigid transforms, explicit sketch ownership and world sketch coordinates | External references, flexible components, joints and grounding semantics |
| Dependencies and ownership | Paired forward/reverse tables and explicit component-scope references for observed feature records | Other edge meanings and unobserved scope datum layouts |

Internal lengths use centimetres and angles use radians in the recovered numeric records. Display units such as `mm` are separate. Sweep path fractions are unitless. Sketch-local geometry remains available alongside decoded component-coordinate values.

Non-distance holes can retain an inactive saved depth. It is reported as cached data, never as the active extent. Hole diameters are stored model parameters; thread definitions and their effect on the physical hole are not yet decoded. The six hole reference files compare these settings, position and direction directly with Fusion's API.

`hole-placement-decoding.json` compares five more hole definitions, including reversed distance/through-all, one/three sketch points and a circular-edge center. Every stored position is checked against API or actual input coordinates. Placement mode, direction and diameter are compared with the completed feature. Sketch-point association records/tags and center descriptors are preserved, without claiming the full associative definition. The axis proxy's stored origin can use a different context from the final hole position and is retained separately; general assembly coordinate contexts remain unverified.

`body-tool-decoding.json` compares 12 scale, mirror and shell examples with API values, including explicit combine/tangent contrasts and a separate scale factor. The first body-tool generator run retained seven exports and two API-property errors; the corrected run exported all nine cases. Scale-point evidence comes from the actual input construction point because reading the completed feature's point requires rolling its history back. Inactive shell thickness bindings are represented as null rather than invented numeric parameters.

`pattern-decoding.json` checks six rectangular patterns with one/two directions, spacing/extent modes and independent symmetry flags. A missing second-axis selection and its stored zero vector remain explicit: Fusion's API may supply a default direction that is not present in that native field. Quantities and distances are reported as parameters, without claiming a complete instance-placement algorithm.

`edge-tool-decoding.json` compares 15 fillet/chamfer examples, including multiple sets, curvature continuity and a changed tangency weight. Each edge set resolves its own parameter bindings and selection owner. Variable fillets currently support endpoint radii only; asymmetric flip state is explicitly unresolved. Chamfer definition records preserve their independent modes and observed flip flags. None of this reconstructs the selected BRep edges.

`split-decoding.json` compares five planar split cases: extension on/off, origin and offset construction planes, and one/two target bodies. The tool proxy's stored operation flag agrees with the feature, and both input proxy owners are checked. Counted target descriptors remain explicit without claiming decoded body topology or regenerated result solids. Selection proxies with optional numeric attributes use the same bounded list reader as ordinary proxies.

`sketch-tool-decoding.json` compares ten offset/pattern cases, including both offset signs, closed rectangle/circle offsets, full/partial/symmetric circular patterns and spacing/extent rectangular patterns. Relationships use explicit entity lists and numeric bindings; stored curve positions are independently compared with the API. The first export retains three documented-null-direction API errors; a focused retry creates those three rectangular cases using numeric property setters. The decoder reports these relationships under sketch `constraints`, with recognized-but-unsupported layouts listed in `sketch_decoding.tool_constraints.unresolved`. Offset fixed/construction state, secondary tag semantics, topology-match flags and instance suppression remain partial.

`revolve-mode-decoding.json` checks ten angular revolve examples against API values. Symmetric extents store equal along/against angle bindings; asymmetric two-sided extents store different angles. These are reported separately rather than silently treating one as the complete sweep. Full-turn classification currently applies only to observed one-sided extents. Axis selection follows the decoded variable-length reference fields, including records with optional attribute headers.

`revolve-to-decoding.json` checks one/two-sided construction-plane extents against three API input definitions. Target planes resolve through explicit selection chains. An inactive `AlongAngle` parameter remains cached data and is not reported as an active angle. Direction hints, the resulting sweep angle and general BRep-face targets remain unresolved.

`asm-decoding.json` checks six `.smb`/`.smbh` body/history streams from three existing files. The token reader reaches the final marker and exact EOF, preserves contiguous record boundaries, and finds all non-null pointer indices within each record table. This validates token framing, not the identity of the final visible solid. A blob can contain several intermediate bodies. History header values are retained separately and must not be assumed to use the same coordinate context as final geometry.

`brep-decoding.json` adds typed topology links, reciprocal ownership, closed coedge rings and vertex positions. API evidence from `breptruth-2dfc22bbf5eb` comes from new local imports of three study-owned files. Stored graph candidates match the counts and vertex coordinates of all six resulting API bodies (a hole, a filleted body and four split pieces). These are diagnostic candidate matches, not proof of persistent native body identity. Some history records describe other states and remain unresolved rather than being silently merged into the candidate graph. Body transforms and raw header unit fields are retained without applying a guessed conversion.

`body-binding-decoding.json` follows a typed design mapping table to an exact history-blob filename and explicit native body objects. Its opaque handles must not be used as ASM record indices: the observed single-body fillet stores handle `2`, while its matching leading ASM body is record `1`. When the declared leading roots fit the mapping count, the reader provides an **experimental ordered-root candidate** for each entry. Candidate geometry matches all six API bodies in the focused evidence, but broader ordering/component/history variants remain unverified. Stored tags such as `0_275` are internal tags, not recovered user-visible body names. These tables appear under each design stream's `body_blob_bindings`.

The default JSON includes ASM summaries and stored body graphs under `asm_decoding`. To inspect full typed records and decoded topology nodes, run `asm_records.py --records --zstd-library "$FUSION_STUDY_ZSTD" path/to/sample.f3d`. Output can be large. Unsupported tags stop that blob's inspection at an explicit offset and preserve the last complete-record position.

ASM tag meanings and field order were referenced from the primary ezdxf [constants](https://github.com/mozman/ezdxf/blob/master/src/ezdxf/acis/const.py), [reader](https://github.com/mozman/ezdxf/blob/master/src/ezdxf/acis/sab.py) and [entity definitions](https://github.com/mozman/ezdxf/blob/master/src/ezdxf/acis/entities.py). Accepted 64-bit widths and token signatures were checked against local Fusion samples. This standalone reader does not import ezdxf or supply a geometry kernel; the upstream [ACIS documentation](https://ezdxf.readthedocs.io/en/stable/acis.html) also describes its limited entity coverage.

`assembly_decoding.occurrence_paths` expands native occurrences through their parent components. Repeated instances share component definitions but have separate world transforms. A modeling feature's input-sketch component is recorded as source context. Its parent component is resolved separately through an explicit dependency-scope edge and typed component datum when that layout is recognized. Sketch ownership provides an independent consistency check.

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

Useful next areas are broader dependency semantics, external/flexible assembly definitions and joints; broader timeline composition; general sketch pattern/offset variants; feature-specific selections and modes; and BRep topology. A native writer, full geometry regeneration, and integration with the Kit translation pipeline remain separate unfinished work.

Use small controlled API examples, vary one setting where practical, and retain unknown fields. Prefer metadata/class identities and explicit references over byte searches or inference from geometry alone.
