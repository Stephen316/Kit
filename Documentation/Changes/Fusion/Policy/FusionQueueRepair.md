# Fusion queue repair

The first merge queue run of PR #92, [run 43530545010](https://github.com/TryUniCAD/Kit/actions/runs/43530545010), failed `CI Agg`.
PR CI does not run the full test suite or the security scans, so these findings were new.
This entry records each finding and its repair.

## Import cycles

CodeQL reported 325 blocking findings. Of these, 302 were `py/unsafe-cyclic-import` and 6 were `py/cyclic-import`, from 11 cycles.
CodeQL counts imports under `if TYPE_CHECKING:` and imports inside functions, so moving an import does not remove a cycle.
Each cycle now runs one way. No cycle is suppressed.

- Recursive value records take a type parameter. `EntityCodec/Model` containers are generic over `MemberValue`, and `ValueTypes` alone closes the recursion as `KEntityValue`. The graphics records, `FieldSpec`, `VertexRecipe` and `FieldJson` follow the same pattern.
- BrepCodec typed records subclass the empty leaf `TypedBase`, so the grammar value union does not import the record modules.
- Recursive functions take the dispatcher as an argument. `ConvertFields`, `ConvertGroups` and `ConvertSeries` receive `ConvertValue`. `SceneCodec` receives its object and override readers.
- `MeshState` holds the mesh stream state that `TransferSpanMut` and `FinishStreams` read.
- The interchange access mixins cast `self` to a small `Protocol` of the fields they read, instead of importing `CadDocument`.

Class names and modules are unchanged, so saved Fusion semantic state still decodes.
The repair also reads and re-emits all 1,630 graphics scenes found under `re/` with identical digests.
See [the gotcha](../../../Gotchas/Ci/TypeCheckingImportCycles.md).

## Other CodeQL findings

Ten type aliases such as `KJsonValue` are imported by other modules, but CodeQL reports them as unused globals.
They carry the `lgtm[py/unused-global-variable]` marker that `main` uses for `KSourceType`.
`HistoricBundle` ends in `pytest.skip`, so it carries the `lgtm[py/mixed-returns]` marker.
A redundant page map encoding before the size loop in `SizePages` is removed.
The `TypedRecord` protocol body raises `TypeError`, like `RecordMaker`.

## Scanners

- Semgrep: the two vocabulary readers load their data with `Path(__file__)`, like the other vocabulary readers, instead of `importlib.resources`.
- dlint: `TextElement` builds an `Element` and sets its text with `setattr`, as the FreeCAD archive does. The material XML parser and emitter imports carry `noqa: DUO107`, like `SafeParsing`. The parser already rejects declarations and processing instructions.
- Gitleaks: `NOD/AcDbVariableDictionary` in `SheetDefaults.json` matched the generic API key rule. It is a DWG named object dictionary key. The Gitleaks allowlist accepts `NOD/` keys made of letters and underscores. A `.gitleaksignore` fingerprint cannot cover it, because the queue commit changes with each candidate.
- OSV-Scanner: the `opentelemetry-api` advisory comes from `main` and is repaired in PR #111.

## Tests

- `PackSections` used `pass` in an exception handler. It now uses `contextlib.suppress`.
- `SegmentKind` now includes the two drawing segments. Tests that read every segment of a design archive iterate `KCoreSegments`. See [the gotcha](../../../Gotchas/Conversion/Fusion/FusionDrawingSegmentKinds.md).
- The metadata wire test model now has one version context, because the reserved word counts the contexts that follow it.
- `MaterialRecord` is exported by the new `interchange.materials` facade, and the compatibility snapshots include it and the `materials` field. See [the gotcha](../../../Gotchas/Packaging/InterchangeExportSnapshots.md).
- The swap matrix check excludes `fusion.f3d`, because the Fusion writer accepts only documents created through Fusion. See [the gotcha](../../../Gotchas/Conversion/QualifiedWriterSwaps.md).
- `TestPendingGate` timed out without output on one run and passed on the same tree before. It is unchanged. See [the gotcha](../../../Gotchas/Ci/AggregateGateTimeout.md).

## Verification

CodeQL CLI 2.27.4 with `CodeqlConfig.yml`, `PythonMaximal.qls` and the Kit model pack reports 0 blocking results on this branch and on `main`.
`ruff`, `black --check`, `mypy`, `pyright`, the steering and rationale checks, the CI dlint command and the CI Semgrep command pass.
Gitleaks 8.30.1 reports no leaks in the changed files.
No tests ran locally. The next queue run gives the test suite verification.
