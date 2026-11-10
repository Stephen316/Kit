<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Saved corpus and import provenance

[Fusion feature index](../README.md)

## Import provenance

Paths beginning with `Study/` are relative to `re/Fusion/`.

- Source commit: `60ebb72ee7b64a0bf22331012b7c737c0e17d43b`.
- Source tree: `9ffe9d2d126ea4d319aa3ed47e969dbca138ea9e`.
- The import retained the original bytes and names of all 2,556 tracked source files.
- The import merge preserves all 186 commits of the original study history.
- `Study/revolveaxes-36bd04ac77e1/ground_truth.json` adds one required saved
  reference file that the source repository's capture-folder ignore rule omitted.
- The original standalone repository remains available as a local backup.

`Study/` preserves an existing research snapshot, including historical reports,
source hashes, generated capture names, recorded machine paths and known style
findings. Its `.gitignore` retains the original capture rules. The parent
`.gitattributes` prevents line-ending conversion from changing archived evidence.
No nested `.git` directory, installed dependencies or Python bytecode is imported.
The relocation kept the original source formatting, file names and evidence bytes.
Three trailing-space diagnostics in two original executed SDK text snapshots are
retained with their recorded bytes and hashes. Newly written import documentation
is formatted separately.

### Tracked inventory

The UniCAD baseline at `db8ddae6` contains 2,560 files in `Study/`:

| Category                                                    | Files |
| ----------------------------------------------------------- | ----: |
| Python decoder, inspection, capture and validation sources  |   732 |
| Native `.f3d` captures and STL fixtures                     |   739 |
| JSON ground truth, catalogs and generated reports           |   722 |
| Text logs, completion markers and executed source snapshots |   295 |
| Journal and XML records                                     |    69 |
| Study README                                                |     1 |
| Capture manifest and Git ignore rules                       |     2 |

The SDK has 395 Fusion format modules and seven adapter modules. The study
sources have their own legacy style history and are excluded by the project
Black configuration. Historical source hashes refer to the source versions
used to generate the corresponding evidence. Reproduce hash-pinned checks
from those revisions. For current decoding results, rerun the readers or the
health audit and write any new reports to a separate location.

## Relocation verification

At relocation, the imported files matched the source snapshot byte for byte.
All 729 Python modules compile. All 712 saved archives decode from `Study/` and
their complete outputs match the previous committed audit after replacing only
the relocated directory prefix. No geometry or metadata field is removed from
that comparison. The numeric suites pass 33 actual-byte conversion cases and
100 rational-evaluation checks, including five rejection guards and three
native Sweep weight-rescaling controls. The history-dependent Stitch validator also
passes from the imported tree using the preserved original commit objects. These
checks use saved files and make no live Fusion calls. The import does not resolve the decoder's recorded
unsupported features or legacy style findings.

### Saved corpus baseline

The baseline at `8496fc8b` decoded all 712 saved archives and emitted 2,557
feature rows. Counting `kind` across every stream gives 64 named kinds plus
`UnsupportedFeature`. The largest groups are Sketch (1,005), Extrude (526),
ConstructionPlane (151), SurfacePatch (58), and CreateComponent (54).

The 147 unsupported rows span 80 archives. Grouped by `native_kind_label`, they
are Base Feature (54), unlabeled (51), JointOrigin (16), Base Mesh Feature (14),
and Pin, MirrorComponent, Derived Base Feature, and DerivedInstance (3 each).
These counts measure recognition in this capture corpus. A named row can
still contain unresolved selectors, controls, or geometry.

Counting successful feature-level reconstruction attachments separately gives
238 ordinary extrusions, 15 trimmed extrusions, 3 plane-limited extrusions,
15 angular revolves, 14 shells, and 7 scales. There are 26 recognized Revolve
rows overall, including the three [plane-limited cases](Revolve.md#plane-limited-revolve).

The focused workflow was checked against the fixed `FILES` inventories in
`validate_shell_reconstruction_integration.py` and
`validate_plane_extrusion_reconstruction_integration.py`. Load only the
design BulkStream and MetaStream plus `.smb` and `.smbh` members, then build
feature and parameter records from the selected design stream. With the same
body-blob bindings from the full decode, the focused reconstruction matched
the full result on all 15 Shell fixtures and all 8 plane-extrusion fixtures,
including two and five empty controls respectively.

## Study catalog and audits

Saved evidence includes [`decoder-health-audit.json`](../Study/decoder-health-audit.json).

Study scripts, reports and capture paths in this section are relative to [the Study directory](../Study/README.md).

The updated class catalog indexes 461 reference archives and 348 native class GUIDs. These are corpus counts, not a percentage of the complete format or independent validation of every field.

The latest catalog indexes 480 reference archives and 349 native class GUIDs; new native layouts beyond the verified captures remain unresolved.

All 194 API comparisons pass, including the retry's full degree-5 NURBS data with 20 control points, 26 knots and unit weights. The original spline exports retained valid fit-point/parameter evidence but lacked serialized API NURBS vectors; the corrected one-case retry supplies that independent evidence. Eight earlier Line/Circle defaults remain identical, four malformed guards reject, and all six main-reader patterns/additional-geometry outputs match the report. Only successful curve/controller IDs clear earlier rejection entries. Seed Ellipse dependency extra 4 remains a raw uninterpreted value; suppression, multiple curved seeds, other directions, circular spline patterns and solving remain unverified.

At that stage, the catalog indexed 490 reference archives and 349 native class GUIDs. Corpus coverage does not establish complete field coverage or translation capability.

All four latest batches contain completion markers, 17 exports and no recorded capture errors. The reported Fusion crash does not itself identify its cause. These exported files are decoded offline without requiring a live Fusion session. The updated catalog indexes 507 archives and 350 native class GUIDs; neither count is a percentage of the complete format or proof of translation support.

All sixteen component-creation, eight Pin and eighteen topology-context main-reader summaries exactly match their focused reports. The corpus remains 507 archives and 350 native class GUIDs; these new fields use existing exports and do not imply complete feature support.

The three new capture batches completed serially with fourteen exports, no recorded case errors and terminal markers. The catalog now indexes 521 reference archives and 350 native class GUIDs; full-format coverage, persistent topology and translation remain incomplete.

Eighteen new exports bring the corpus to 539 archives and 359 native class GUIDs. One failed API creation attempt is retained alongside the completed successful captures. These counts do not measure complete-format coverage or establish native writing or translation capability.

A user-supplied Fusion crash screenshot was noted during this stage. All further work in this stage uses saved archives; no new Fusion capture is dispatched after that report. The screenshot establishes a crash, not its cause or a decoder failure.

Twenty new successful exports bring the corpus to 559 archives and 369 native class GUIDs. The integrated reader matches saved stage outputs, while 33 representative prior archives retain their existing JSON exactly apart from new summary keys. Initial optional-token getter failures are preserved alongside the successful retries. Archive and class counts do not measure complete-format coverage or establish native writing or translation capability.

This stage uses existing saved archives only. The corpus remains 559 archives and 369 native class GUIDs; coverage additions are structural/parametric extraction, without complete native writing, translation or regeneration. Earlier `*-decoding.json` files are historical snapshots and can retain superseded diagnostic field names.

`saved-variant-integration.json` records focused integration across53 unique saved archives, checks the successful IDs in their main-reader summaries and six unchanged solid-extrusion defaults. No live Fusion capture or external report submission occurs in this stage.

`identifier-provenance-integration.json` records focused main-reader equality checks for seven body-identifier files, six edge-Pipe controls and three face-boundary files. The stage uses existing archives only: no new live capture, restart or external crash-report submission was performed. The corpus remains 559 archives and 369 native class GUIDs; complete-format coverage has no established denominator, and native writing, full translation and regeneration remain unfinished.

`saved-geometry-integration.json` records eleven focused main-reader comparisons across eleven saved archives. All new summaries match their evidence reports and successful Hole/dimension/Silhouette fields are attached. Full edge-Pipe settings remain unsupported even where mixed-root BODY joins now succeed. No live Fusion capture ran; Fusion's process was present but exposed no command window at the read-only availability check. The corpus remains 559 archives and 369 native class GUIDs, without a complete-format percentage, native writer, full translation or regeneration.

`decoder-gap-inventory.json` records a read-only baseline inventory at commit 4835282: all 559 saved archives returned partial results without decode exceptions, in 11.9 seconds. Counts are top-level unresolved diagnostics and can duplicate one underlying gap; they do not measure feature or format completion. The report links the subsequent focused path-plane/root recoveries without claiming a second whole-corpus run. Native writing, full translation, regeneration, exact topology and unobserved feature variants remain unfinished.

Three Chamfer/Fillet control files remain unresolved: named selected faces can survive after their former common edge has been removed, and some Fillet caches have incomplete topology. No nearby edge or unqualified trailing-state record is substituted. Literal historical FPM attribute/descriptor-number coincidences are recorded as research candidates only. All existing secondary context successes and failures stay unchanged. `source-ownership-integration.json` records the focused main-reader checks, six new historical cache contexts, unchanged membership/property controls, seven selected source caches, preserved secondary contexts, corrected cylinder geometry and nine Boundary Fill provenance summaries. The signed plane literal, historical-state replay, general reconstruction, native writing and complete translation remain unfinished. No live Fusion export ran.

Those two vertex exports brought the historical corpus to 561 archives and 963 ASM blobs. At `1bdc9bc`, the attribute snapshot accounted for 29,954 initial custom attributes with zero framing diagnostics: 11,525 ordinary topology names and 18,429 validated metadata/other-definition attributes. Its historical delta attribution subtracted the two captures to reproduce the earlier 559-archive raw inventory exactly. The native class catalog preserved all previous evidence and added only the two captures, remaining at 369 GUIDs and 59 classes with observed semantic labels. `build_class_catalog.py --extend-catalog EXISTING_CATALOG NEW_FILES...` supports incremental extension without re-decoding the old corpus; write its JSON output to a separate file before replacing an input catalog. These are observed-corpus counts, not complete-format coverage percentages.

`modeling-extension-integration.json` compares all twelve new exports and four legacy full-output controls against `142a5ea`. Six Thin Extrudes, eight active wall bindings, three trimmed-profile groups and two custom datum supports publish exactly as their focused evidence. One owned open-Line source failure and three strict profile-membership failures are resolved; all other prior fields, ASM geometry and selection warnings remain exact. At `8c9e3a9`, the corpus contained 578 archives, 983 ASM blobs and 30,630 initial custom attributes, with zero framing/ownership/classification diagnostics. That registry census replayed all 613 records: 454 reciprocal populated, sixty empty and 99 reverse-only. Two later datum captures added six reverse-only rows separately from the original 97-record/179-row proof. `native-naming-registry-original561-manifest.json` pins the historical subset by actual paths and hashes, so future captures cannot enter it accidentally. The class catalog then retained 369 GUIDs and 59 classes with observed semantic labels. Its validator separately qualifies later Circle geometry additions without changing the earlier membership proof.

`advanced-feature-integration.json` compares eighteen saved designs against `8c9e3a9`, including all eleven new exports and four unchanged legacy full-output controls. It qualifies three intermediate fillets, sixteen derived Circle portions, two recovered repeated-source memberships and three AsBuilt features/native-joint routes. All other prior fields, ASM geometry, stored placement labels and unrelated selection warnings remain exact. The three earlier trim cases also retain the `142a5ea` stage boundary after separately qualifying the new Circle metadata. The refreshed corpus contains 589 archives, 1,011 ASM blobs and 31,274 initial custom attributes, with zero attribute framing/ownership/classification diagnostics. All 630 native registries replay: 465 reciprocal populated, 66 empty and 99 reverse-only. The class catalog extends only the eleven new captures, preserves all prior evidence, and now contains 370 GUIDs and sixty classes with observed semantic labels. These counts do not establish complete format coverage, native writing, general feature regeneration or complete translation.

`direction-trim-group-integration.json` compares fourteen saved designs against `2e31d25`: four asymmetric controls with one newly recovered flipped set, three Line groups with twelve portions/24 COEDGEs, and three RigidGroups with seven members and three newly resolved native-joint lookup diagnostics. Four complete legacy outputs remain exact. All other prior fields, ASM geometry and stored placement labels remain unchanged. A separate Rule Fillet control emits no unrelated asymmetric diagnostic. The earlier rectangle also passes the `8c9e3a9` and `142a5ea` stage comparisons after independently qualifying the new Line metadata; original memberships and errors retain their stage-specific proof.

The current metadata/attribute census covers 597 saved archives, 1,033 ASM blobs and 31,823 initial custom attributes, with zero attribute framing, ownership or classification diagnostics. All 645 native registries replay exactly: 473 reciprocal populated, 73 empty and 99 reverse-only. The class catalog extends only the eight new captures, preserves prior evidence, and retains 370 GUIDs and sixty classes with observed semantic labels. These observed counts do not measure a percentage of the complete format or establish native writing, feature regeneration or complete translation.

`remove-mixed-pattern-integration.json` compares twenty saved designs against `751c282`, with eight complete legacy outputs unchanged. It qualifies three mixed memberships, three public removals and five circular tool recoveries; the seed negative acquires only its explicit partial summary. Five corresponding body-input roles and one removal kind update follow independently decoded input lists and classification. All other fields, ASM geometry, stored placement labels and unrelated warnings remain exact. Optional caches avoid repeated main-reader work during development; without caches the validator reproduces exactly the pinned twenty files from local Git and the current reader.

The refreshed corpus contains 609 saved archives, 1,061 ASM blobs and 32,830 initial custom attributes, with zero framing, ownership or classification diagnostics. All 662 native registries replay: 485 reciprocal populated, 78 empty and 99 reverse-only. The class catalog extends only the twelve actual new exports, preserves prior evidence, and now includes 371 GUIDs and 61 classes with observed semantic labels. Failed Boss attempts contribute no archives to these counts. Comprehensive format coverage, native writing, regeneration and complete CAD translation remain unfinished.

At `cd4cad1`, the corpus contained 618 saved archives, 1,079 ASM blobs and 33,348 initial custom attributes, with zero framing, ownership or classification diagnostics. All 672 native registries replayed: 494 reciprocal populated, 79 empty and 99 reverse-only. The class catalog added only that stage's nine exports, preserving prior evidence, and contained 374 GUIDs and 62 classes with observed semantic labels.

At `593bc5e`, the metadata audit covered 627 archives and 1,091 ASM blobs with 33,616 initial custom attributes. It retained ten new unresolved EDGE attribute variants: six no-merge header cases in the Draft files and four chain cases in the Patch files. There are no archive/framing failures, and these diagnostics are not removed by successful native feature-control decoding. All 681 native naming registries replay exactly: 503 reciprocal populated, 79 empty and 99 reverse-only. Corpus and class counts are inventories, not a measured percentage of complete-format decoding or CAD translation.

`draft-patch-mesh-integration.json` compares fifteen saved designs against `cd4cad1`, including six unchanged complete legacy controls. It qualifies three parting-line Draft settings, three B-rep Patch continuity settings, three mesh assets and two native BaseMeshFeature associations. Only the six corresponding old tool errors and the two qualified unsupported-feature classifications are resolved. The separate BaseFeature records, existing SplitFace warnings, all ASM geometry, stored placement labels and unrelated diagnostics remain unchanged. Optional saved-output caches avoid repeated main-reader work; the standalone fallback reads only these fifteen pinned designs. The class catalog adds only the nine actual new exports and preserves prior evidence, reaching 383 GUIDs and 63 classes with observed semantic labels. Native writing, feature regeneration and reliable three-way CAD translation remain unfinished.

`edge-chain-integration.json` compares ten saved default main-reader outputs against `593bc5e`; all ten remain exactly equal, including the six affected designs and four legacy controls. The direct naming-reader reports establish the new chain acceptance separately. The refreshed ASM audit retains the same 627 archives, 1,091 blobs and 33,616 initial custom attributes, with all ten former chain diagnostics recovered: 12,674 owned generic names and 20,942 other validated definitions. There are no remaining framing, ownership or classification diagnostics in this observed corpus. The audit now records the new stitch-hint helper in its source provenance. This bounded chain framing does not establish persistent selected topology, complete format coverage or regenerated geometry.

At `e3b3c24`, `GenerateMeshPlaneCutContrasts.py` was a prepared three-case probe using the active executable bindings, which label these APIs unofficial. The initial targeted command was observed starting, but no generator output or terminal artifact was accessible, so execution and PlaneCut results remain unverified and add no native coverage or archives. The future source uses an absolute-path helper load instead of depending on Fusion adding the study directory to Python imports. No import failure is asserted without a captured exception; no user Assistant dialog was dismissed or Fusion process restarted.

`GenerateApiExecutionStatus.py` records read-only runtime evidence without creating documents. Its saved `apiexecution-e4ea807ccabd` result establishes the executable Fusion 2705.1.30 module path/hash, absence of the study directory from Python imports, and no other current study-script frames. That independently verified execution before the corrected absolute-path PlaneCut probe ran. It does not reconstruct the original missing startup exception or imply that a sleeping computer can execute local work.

The current corpus contains 634 saved archives. The added mesh files contribute no new ASM blobs: the audit still covers 1,091 blobs and 33,616 initial custom attributes, with no framing/ownership/classification diagnostics. All 688 native naming registries replay exactly: 510 reciprocal populated, 79 empty and 99 reverse-only. The original 561-file manifest remains unchanged. These are observed-corpus inventories, not complete format coverage.

At `b8a5580`, `GenerateMeshShellContrasts.py` was a prepared, unexecuted probe: open three-triangle tetrahedra at 0.1/0.2cm thickness and a closed tetrahedron at 0.1cm. That stage checked active executable API signatures and source boundary counts without adding Shell archives or native coverage.

The recorded class catalog covers 707 archives and 403 distinct native class
GUIDs. The October 24, 2026 audit also ran five additional captures, for
712 archives in total. The execution check covers those saved inputs and leaves
the catalog scope unchanged. The reference layouts came from Fusion `2705.1.30`.

## Decoder health audit on 2026-10-24

`decoder-audit-summary.json` separates functional results from comment compliance. All 729 Python modules compile, and all 712 saved archives pass the full reader with finite JSON numbers and unique feature identities within each stream. Their complete outputs are byte-identical to a pre-repair acquisition from `556c3ef`. The broader checks pass 132 standalone validators, 22 additional geometry/native-reconstruction suites and two new numeric suites. This verifies the saved examples; it does not establish full format coverage, general history replay, native writing or absence of every possible bug.

Finite native parameters and Circle radii now reject overflowing millimetre/degree conversions through existing explicit diagnostics. Rational curve, derivative and tensor evaluators retain their ordinary floating fast paths and retry unsafe projective arithmetic with Decimal inputs converted exactly from binary64. The fallback preserves subnormal and extreme mixed weights, large finite knot intervals and previously accepted higher degrees. `validate_numeric_conversions.py` checks 33 actual-byte cases; `validate_rational_numerics.py` checks 100 numeric comparisons, five rejection guards and three native Sweep weight-rescaling controls. Both suites also pass on Python 3.12 in addition to the system Python 3.9 audit. The parameter-only entry point now merges quoted Text-literal dependencies consistently with the full reader.

Seven older validators were repaired without weakening decoded-field checks: newer supported spline/Cut geometry receives direct coefficient or API-array corroboration; canonical and Mirror-owned creation routes remain separate; quoted Text dependencies are tested explicitly; Stitch targets come from a fixed committed inventory; and variable-blend comparisons sample only inside the actual common curve/UV domain. Native parameter intervals remain unchanged, and out-of-domain evaluation still rejects. Original capture archives and historical committed reports were preserved.

The canonical comment reference is TryUniCAD/Kit commit `e64a368a2b644cc223d69556c5fda58f60175b62`, specifically `.kiro/steering/RationaleComments.md` and `tools/steering/SteeringCompliance.py`. Its rationale and comment checks pass all 176 required sites in the 15 changed Python files. The full 299-file decoder/support audit still reports 2,069 rationale findings and 262 other comment findings. A complete comment migration remains unfinished; no full style-compliance claim is made. Docstrings used by CLI help and scientific provenance remain intact.

`audit_decoder_health.py` reruns syntax, saved-file execution, strict JSON, feature-identity and syntactic comment checks:

```sh
/usr/bin/python3 audit_decoder_health.py --zstd-library "$FUSION_STUDY_ZSTD" --output /private/tmp/fusion-decoder-health.json
```

The command reports functional and comment status separately and exits nonzero while either fails. Its detailed committed result is `decoder-health-audit.json`; the known comment migration produces a style failure even when all functional checks pass. The optional `--baseline-directory` accepts the temporary compressed pre-repair outputs used for this audit. Additional canonical comment findings and focused-suite summaries are retained in `decoder-audit-summary.json`. No live Fusion calls or remote writes were made.
