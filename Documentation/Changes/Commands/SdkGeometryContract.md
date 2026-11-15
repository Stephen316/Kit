# Require an SDK regeneration contract for geometry conversion

`kit convert` now requires local body or B-rep data to match an existing qualified Fusion authoring or native-state contract.
Generic typed feature histories, including Boolean and bound-scale histories, are not geometry qualification by themselves.
Without a supported regeneration contract they remain inspection-only while format research is unfinished.
Embedded geometry documents are checked separately. Current sketch, parameter,
and assembly eligibility also follows the stricter [model history](ParametricModelGuard.md)
and [placement](AssemblyPlacementGuard.md) guards.

The CLI uses the SDK's `CheckContract`, `MakeFusionDoc`, `ProjectNative` or `ProjectVendor`, and `EncodeDocument` validation.
It regenerates the canonical graph and compares every semantic data field before invoking the selected writer.
The comparison preserves geometry, controls, names, identities, units, diagnostics, capabilities, scalar types, tuple/list/set distinctions, and mapping contents.
Known `WireEnum` values compare with their canonical text spelling, and explicit feature order governs timeline comparison.
Only record provenance/attribute bags and document source/root metadata are excluded from this core comparison.
Retained-byte and unsupported-kind checks run first over the complete original document.

The comparison uses temporary snapshots; it never removes fields from the document passed to the writer.
Plain text/hash provenance remains available in JSON output.
Each writer retains its own full fidelity and native-transfer checks, so the comparison does not authorize dropping extra data for a native destination.
SDK geometry-contract validation requires Python 3.14 and imports its archive helpers lazily.
Python 3.11 inventory and bodyless workflows retain their existing startup path and graceful refusal behavior.

Process cases now refuse the earlier two-input generic Boolean join and a coincident-input cut retaining a nonempty B-rep.
Another case updates the qualified authoring specification, controls, and body summary while retaining stale B-rep geometry.
Root/nested cases validate the neutral source and preserve source files, missing/existing destinations, and inspection.
Provenance fixtures retain their qualified contract, and known constraint-kind fixtures use the SDK's actual constrained-rectangle history.
Existing authoring/native Fusion round trips and qualified assembly children remain required.

No new Boolean engine or CAD evaluator was added.
Canonical SDK consistency does not establish native application loadability, rebuild behavior, or measured parametric acceptance.
No local tests, decoding, SDK generation, or CAD applications ran.
Anchored Black and Prettier formatting passed.
Pyright reported zero errors, mypy reported no issues, and steering compliance passed for the 14 changed Python files.
Pyright also reported three unsupported settings already present in the repository configuration.
Tracked-tree path policy and staged whitespace checks passed; runtime evidence remains pending remote CI.

See [command usage](../../Tasks/CommandLine.md) and [the stale-geometry gotcha](../../Gotchas/Conversion/Commands/TypedHistoryCanRetainStaleGeometry.md).
