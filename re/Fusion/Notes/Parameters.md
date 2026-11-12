<!--
This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Parameters and formulas

[Fusion feature index](../README.md)

See [numeric parameters](../../../src/convert/formats/Fusion/ZipParameters.py) and [formula tests](../../../tests/convert/formats/FusionFormulaTests.py).

## SDK coverage

`convert.formats.Fusion.ZipParameters.ReadZipParams` projects indexed
numeric parameters into Kit's neutral `Parameter` records. It retains native
expression text, display units, binding IDs, and source spans. Values use
their stored radians or centimetres where applicable. Feature-bound
parameters retain reference roles while their neutral feature owners are
being mapped. The SDK verifies each native binding's class, parameter
reference, repeated owner ID, and cached value before recording the native
owner and binding span. A rejected binding leaves the numeric value
available and produces a diagnostic. Unsupported registered parameter
records also produce diagnostics. The SDK projection matched the study on
2,607 numeric parameters across the 712 tracked archives and another 51
across the 13 Fusion 2706 captures. All 2,593 feature-bound parameters
matched the study's native owner IDs.

`convert.formats.Fusion.ZipHistory.ReadZipHistory` projects native history
references into ordered Kit feature steps, keeps histories separate by
owner, and retains the original group membership and collapse state.
It links numeric parameters to feature steps through verified bindings.
The SDK matched the study on all 779 history sequences across 725
archives, including 3 groups. It projected 2,524 steps and linked
2,587 parameters to a unique step. A parameter with no unique projected
step retains its native owner ID. Feature names and kinds are currently
projected for the observed Extrude, Revolve, and construction-plane
classes. Other entries retain native identity and provenance. Feature
definitions, geometry, and default adapter integration remain open.

`convert.formats.Fusion.ReadFusionDoc` exposes this history through a
validated `CadDocument`. It accepts a path or archive bytes and uses the
same optional Zstandard callback as `ReadDesignZip`. When more than one
history is present, pass the native `HistoryId` to select one. The resulting
document carries a projection configuration, a partial-coverage diagnostic,
and the original archive as a native document payload. It can round-trip
through the Kit JSON reader and writer. The SDK verified document projection
for all 766 histories in the tracked corpus.

For a verified single-component parameter collection, the document reader
can derive arithmetic dependencies from exact user-parameter names. It
requires an acyclic chain, compatible units, and an evaluated result that
matches the saved numeric record. The supported grammar covers grouping,
unary signs, and addition, subtraction, multiplication, and division.
Ambiguous names and unsupported expressions retain their original text.
The Fusion records store the formula and evaluated value. The dependency
identities come from resolving the formula against the native name registry.
Across 712 tracked archives, eight formulas qualified and all eight wrote as
native spreadsheet cells. Sixteen archives still require explicit history
selection because the assembly projection is incomplete.

FreeCAD spreadsheet export rewrites proven operand names to their exact
parameter aliases. FreeCAD 1.1.3 verified four arithmetic captures against
the saved Fusion API results and recalculated each result after changing an
input. The `expression_depth` capture uses the same spreadsheet bindings
to drive its native circular extrusion.

Standalone Fusion parameter workbooks with a fully supported formula graph
also support saved driver edits. Kit reads the edited literals, recalculates
the dependent values, and retains the original Fusion formulas and parameter
identities. A changed formula, incompatible unit, or added workbook content
fails readback. Standalone archives exported before the workbook binding was
introduced still read as their original snapshots.

FreeCAD 1.1.3 saved and reopened six controls covering four arithmetic
formulas and two equal-value inputs with distinct identities. Kit read back
the changes with the original dependency IDs and Fusion archive bytes. In
the product control, changing the width to 8 mm produced 21 mm. After
re-export, changing the scalar to 3.25 produced 27 mm.

## Numeric parameter field map

This map covers the payload of native class
`7A6A3D31-BE74-4E19-9115-20642944C2E4` when its value type is numeric.
Offsets start at the numeric body, four bytes after the SDK's
`RecordSpan.PayloadOffset`. Integers and binary64 values are little-endian. A counted string has a 4-byte unsigned UTF-16 code
unit count followed by twice that many bytes of UTF-16LE text.

| Field                  | Byte offset              | Width in bytes | Type           | Interpretation                                                                                         |
| ---------------------- | ------------------------ | -------------: | -------------- | ------------------------------------------------------------------------------------------------------ |
| Header                 | 0                        |             12 | bytes          | Seven zero bytes, `06`, then four zero bytes.                                                          |
| Comment                | 12                       |       variable | counted string | May be empty. The reader accepts CR, LF and TAB here.                                                  |
| Native parameter index | End of comment           |              4 | u32            | Stored index compared with the binding index for bound parameters.                                     |
| Binding reference      | End of index             |        1 or 11 | tagged field   | `00` for an unbound user parameter. A bound parameter stores `01`, a u64 object ID and two zero bytes. |
| Expression             | End of binding reference |       variable | counted string | Saved expression text.                                                                                 |
| Numeric metadata       | `M`, end of expression   |       10 or 11 | bytes          | See the layout comparison below.                                                                       |
| Role                   | `M + 10` or `M + 11`     |       variable | counted string | For example, a feature binding role or `User Parameter`.                                               |
| Reserved text          | End of role              |              4 | counted string | Empty for numeric records.                                                                             |
| Display unit           | End of reserved text     |       variable | counted string | Display label such as `mm` or `deg`.                                                                   |
| Parameter name         | End of display unit      |       variable | counted string | Stored parameter identifier.                                                                           |
| Cached value           | End of name              |              8 | binary64       | Finite value. Lengths use centimetres, angles use radians, and scalars are unitless.                   |
| Trailer                | End of cached value      |             12 | bytes          | `00 01 10` followed by nine zero bytes in the SDK's supported layouts.                                 |

| Metadata field  | Byte offset | Width in bytes | Type  | 10-byte layout                                                                     | 11-byte layout                                      |
| --------------- | ----------- | -------------: | ----- | ---------------------------------------------------------------------------------- | --------------------------------------------------- |
| Value type      | `M + 0`     |              4 | u32   | `0` for numeric.                                                                   | `0` for numeric.                                    |
| Opaque metadata | `M + 4`     |              3 | bytes | Preserved as stored.                                                               | Zero in observed captures.                          |
| Favourite flag  | `M + 7`     |              1 | byte  | Controlled captures establish `0` and `1`. Other model values remain unclassified. | Zero in observed captures.                          |
| Opaque metadata | `M + 8`     |              2 | bytes | Preserved as stored.                                                               | Zero in observed captures.                          |
| Extension       | `M + 10`    |              1 | byte  | Role count starts here.                                                            | One extra zero byte. Role count starts at `M + 11`. |

The tracked [expression-depth capture](../Study/holdouts-f8c508a73323/expression_depth.f3d)
exercises the 10-byte layout with both unbound and feature-bound numeric
parameters. [Parameter text contrasts](../Study/parameter-text-decoding.json)
isolate the favourite flag. The [13 Fusion 2706.1.17 Revolve controls](Revolve.md#plane-limited-revolve)
exercise the 11-byte layout. Their 51 bound parameters matched the captured
API names, roles and numeric values.

The SDK tries the role at `M + 10` first. It retries at `M + 11` only
when role decoding fails, a binding reference is present and all 11 metadata
bytes are zero. The reader still validates the remaining fields and trailer. The meaning of
the extra zero byte remains unresolved. See the
[SDK numeric decoder](../../../src/convert/formats/Fusion/NumericParam.py)
and [numeric proof tests](../../../tests/convert/formats/FusionProof/FusionNumberTests.py).

## Saved study coverage

Saved evidence includes [`parameter-table-decoding.json`](../Study/parameter-table-decoding.json).

| Area                       | Observed support                                                                                                                                                                                                                                                                                                      | Open work                                                                                                         |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Parameters                 | Numeric/Text model and user values, stored expressions, derived arithmetic and observed unary-function references, user/model comments/favorites, captured second editable Text binding and observed multiline Text strings, display units, explicit feature-binding references and reciprocal collection/name tables | General expression evaluation, explicit native expression edges, other types/control characters and name variants |
| Dependencies and ownership | Paired forward/reverse tables and explicit component-scope references for observed feature records                                                                                                                                                                                                                    | Other edge meanings and unobserved scope datum layouts                                                            |

### Saved study findings

Study scripts, reports and capture paths in this section are relative to [the Study directory](../Study/README.md).

Internal lengths use centimetres and angles use radians in the recovered numeric records. Display units such as `mm` are separate. Sweep path fractions are unitless. Sketch-local geometry remains available alongside decoded component-coordinate values.

`parameter-table-decoding.json` checks 335 native parameter collections and 1,188 named numeric records across the existing 310 archives. Counted name-registry dependencies, collection members, numeric names and reciprocal ownership agree; registry order is retained separately from collection order. These corpus checks establish structural consistency, not independent API verification of every value. The expression holdout now recovers the unbound `probeDepth` user parameter instead of rejecting its absent feature-binding slot. Its stored `9.125 mm` expression/value match the generator's requested input, while saved API truth checks the dependent extrusion's expression and depth. Five malformed cases are rejected. Both reader entry points expose `parameter_tables`; the main reader also retains user records under `unbound_parameters` because they have no feature binding. This initial stage had one user-parameter example; no expression evaluator or expression dependency graph is claimed.

`user-parameter-mode-decoding.json` expands that initial single example with eight new files and ten parameters, checked against 71 actual API getter comparisons. Lengths in millimetres/inches, angles, unitless values, multiple parameters, a dependent expression, Unicode comment text, favorite state and a Text value are recovered. Parsing the variable-length comment fixes offsets that previously assumed it was empty. A text parameter exposes its stored expression and text value without assigning the numeric placeholder as its value. Six malformed fields are rejected, and parameter/table framing remains valid across all 344 current archives. Captured API dependency names are reference evidence only; expression evaluation and native dependency edges remain unavailable. This earlier stage left model favorite flags and multiline comments unverified; the later text stage below adds observed variants. Other name/value variants remain partial.

`parameter-dependency-structure-audit.json` compares saved API dependency/dependent getters with native tables across the eight existing user-parameter captures (ten parameters). In `dependency_chain.f3d`, API `probeResult` depends on `probeWidth` and `probeScale`, but paired native graph 29 contains zero edges. Collection 16/name registry 17 include all three parameters; their membership references do not establish the two expression relationships. This prevents interpreting generic graph or registry membership as expression dependencies. Other native record families may hold more data; no general absence claim or expression parser/evaluator is implied.

`parameter-text-decoding.json` adds five successful exports in `parametertexts-d16f951482fc`, with 40 API comparisons, ten earlier user parameters preserved and four focused guards. Numeric user/model comments and Text values/expressions retain observed CR, LF and TAB characters. The generic string reader remains strict by default; only parameter comment/Text fields opt in, and numeric expressions containing controls remain unsupported. Model parameters now expose their comments and favorite flag: a controlled false/true pair changes only metadata byte 7 in the numeric parameter payload. Unknown model favorite values retain null plus a status and raw metadata. Expressions are retained without evaluation or inferred dependency edges.

`expression-dependency-decoding.json` adds six successful exports in `parameterexpressions-3ddbef2b20bd`, containing 24 parameters. `decode_expression_dependencies.py` fully parses 22 numeric arithmetic expressions and derives references through reciprocally owned parameter-name tables; all reference sets match actual API dependency getters. It preserves repeated name occurrences separately from unique reference IDs, unary signs, parentheses, numeric spellings and bounded unit spellings. At that stage Function and Text examples remained explicitly unresolved; the function stage below adds observed unary calls. Five guards reject unsupported/partial syntax and ambiguous names. Both main and parameter-only readers expose the same `derived_expression_dependencies` summary. This derived view is separate from explicit native graph edges and performs no expression evaluation, dimensional validation or dependency ordering.

`parameter-function-decoding.json` adds four successful exports in `parameterfunctions-bc10224394fe`, extending the derived arithmetic reference parser to observed unary `sqrt` and `abs` calls, including nested calls and unary signs. Twenty-seven parameter reference sets and stored expressions match actual API getters across the four new and three earlier archives, with identical summaries from both reader entry points. The earlier `sqrt(probeScale)` holdout now derives its reference; Text stays explicitly unresolved. Five guards reject unknown functions, extra/missing arguments, trailing syntax and excessive nesting. `validate_parameter_function_modes.py` reproduces these focused comparisons. Calls are retained as syntax trees; no function evaluation, unit validation, native expression-edge decoding or general function support is claimed.

The canonical parameter reader now accepts observed bound Text model parameters with strict reciprocal typed bindings: cached text, parameter ID, stored index, repeated sketch-feature owners and bookkeeping link must agree. Text values retain multiline characters and carry no numeric placeholder value. Both main and parameter-only readers decode their reciprocal name tables, and the main reader attaches Text parameters to their owning sketch. Changed opaque text controls reject; unvaried underline, combined styles, flips, alignment, character spacing and fixed/reference state remain unresolved. Path text, glyph/font rendering, expression evaluation and native regeneration remain unsupported. Archives without native Text return before repeating parameter decoding.

`parameter-text-binding-decoding.json` fixes a missing canonical Text parameter, rather than changing registry names. The second editable Text binding uses slot3 with paired height slot2; the old Text parser assumed slot1. A separate validator checks the owned Text source, sketch binding list, Text2 role/index/value copies, height parameter and bookkeeping. Canonical parameter d8 now matches the actual API Text2 value UCAD; its reciprocal name table and ten numeric dependency results recover automatically. Parameter-table errors now distinguish missing decoded records, ambiguous matches and actual name disagreements. The original slot1 branch stays unchanged.

The same parameter report validates 27 exact single-quoted Text literals across 26 saved files, including multiline/Unicode text. Literal spelling must match the cached value and a unique reciprocal name-table scope. Such literals have no parameter references; a saved expression containing the numeric parameter name probeWidth still has an independently recorded empty API dependency list. Four binding guards, four literal-grammar guards and 25 unchanged canonical parameter controls contribute to 179 focused checks. Main output exposes `text_literal_dependencies` and merges successful literal results into `derived_expression_dependencies`. Concatenation, escaping, conditions, other binding layouts, general expression evaluation and native dependency tables remain unsupported.

`context-parameter-integration.json` records main-reader comparisons and revisits the saved files with the 96 targeted diagnostics from a fresh corpus audit. Fifty of those diagnostics are now resolved; 46 cache-only selection contexts remain. The three historical Silhouette controls allow only the numeric-collision diagnostic label correction documented by the previous stage. This is progress within the reference corpus, not a percentage of the complete Fusion format. No live Fusion capture was dispatched; the corpus remains 559 archives and 369 native class GUIDs, with writing, full translation and regeneration unfinished.

`parameter-native-link-audit.json` audits eleven existing parameter-only archives: forty-three parameters and sixteen actual API dependency edges. Literal parameter-ID occurrences belong to object headers, collection membership and name/registry tables, including unused and quoted-name controls. Empty feature-dependency tables do not establish user-parameter expression edges. No native expression-edge decoder is claimed; alternate namespaces, implicit representations and rebuilding dependencies from expression text remain possible.

`GenerateParameterIdentityContrasts.py` prepares the next expression-link experiment without dispatching it. One owned document retains alpha, bravo and result while result's requested expression changes through `10 mm`, `alpha`, `bravo`, `10 mm`. Requested text length and numeric value remain constant; actual expression spelling, values and dependency/dependent getters are recorded independently before each local export. Journals preserve partial failures. The generator compiled, but no new exports or stable native-ID observations exist yet.

`parameter-expression-record-decoding.json` adds a full indexed-payload contrast, without a duplicate runtime expression decoder. Forty-three user-parameter payloads across eleven saved archives are partitioned and replayed exactly, with their actual API expression/cache values checked. Ten comparable exports align all 221 indexed payloads: 213 remain byte-identical, while the result parameter and seven other identities vary. The parameter variation is accounted for by existing expression/Text/unit/value-cache fields. Framed UUID/configuration/date strings explain other portions, but twenty changing bytes in two non-string spans remain explicitly opaque. The 2,210 payload comparisons and three malformed guards constrain the next same-document identity contrast; they do not prove the absence of native dependencies. Actual sixteen API dependency edges stay separately labelled, and native operand/dependency records remain null. No live experiment was dispatched.

`GenerateParameterIdentityContrasts.py` produced four actual exports from one owned document in `parameteridentity-8fc83529b236`, changing only `result.expression` through `10 mm`, `alpha`, `bravo`, and `10 mm`. All expressions have equal length and cached numeric value; actual API dependency getters separately record the two reference states. `parameter-identity-contrast-decoding.json` compares all 220 indexed record identities across four exports. Exactly six payload identities vary, and the final literal restores the entire result-parameter payload. Reused parameter readers replay all twelve user-parameter records; no new native operand or dependency-edge encoding is established. A reciprocal component-scope/support route frames one raw u64 in an exact39-byte support record. Interpreted conditionally as Unix microseconds, all four values fall within captured assignment/computation journal intervals. `scope_update_times` retains that hypothesis separately from the raw value; native epoch/unit and the specific lifecycle event remain unknown. Seven malformed guards, zero/overflow value controls and an older saved fixture pass.
