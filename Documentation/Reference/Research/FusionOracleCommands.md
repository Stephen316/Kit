# Fusion local oracle commands

## Scope and evidence

An installed Fusion process can execute an isolated Python capture script through its existing frontend command bridge.
This research used Fusion `2706.1.17` on macOS arm64 after explicit authorization for controlled local oracle captures.
It did not require a GUI driver, a registered add-in, or enabling the Fusion MCP server.

The bridge is an internal interface shipped with Fusion, reached through a local Chromium debugging transport.
It is not established here as a supported public external automation API, a headless mode, or a stable interface across releases.
Kit's production reader and writer must remain independent of the Fusion runtime.
Successful oracle execution is evidence about the vendor's data model; it does not establish independent generation, complete decoding, or target-application acceptance.
See the [persistence data model](FusionDataModel.md) and [oracle requirements](Oracles.md).

The inspected installation was under:

```text
~/Library/Application Support/Autodesk/webdeploy/production/b43a07003c01dd54425db484d23b1c5e6248a21d/Autodesk Fusion.app/Contents
```

Paths below are relative to that `Contents` directory.
An earlier version of this reference also cited native library symbols and addresses from binary inspection.
That material was removed at the tip and remains in git history.
Only the behavior seen in captures is described here.

## Dispatching a capture script

The running process exposed a Chromium target list at `http://127.0.0.1:9766/json/list`.
The Fusion home target had a URL under `https://ui-dls360.autodesk.com/fcdr/fusion-home-tab/`.
Its target identifier and WebSocket URL are session-specific and must be discovered rather than copied from a previous capture.
The existence of this listener in the studied session does not establish that every installation enables it.

The installed home frontend contains the native bridge wrapper in:

```text
Resources/FusionCDEHostApps/fusion-home-tab/bundle.aae5d9dd82739a0c3062.js
```

The frontend waits for `window.neutronJavaScriptObject` and serializes command arguments as JSON.
The following expression, dispatched in that target through its local debugging transport, successfully reached Fusion's Python runtime:

```javascript
window.neutronJavaScriptObject.executeCommand(
  "RunScriptCommand",
  JSON.stringify({ Path: "/absolute/path/to/Capture.py" }),
);
```

The working call passed `Path` as a root JSON property containing a string.
Other spellings and argument shapes were not tested.
Supplying a nonempty path avoids the command's file dialog.
The command is registered in `Libraries/Neutron/Neutron/UI/Commands/Resources/CommandDefinitions/CommandDefinitions.xml` with identifier `RunScriptCommand` and the description “Run a python script”.

### Completion and Python context

The JavaScript call dispatches asynchronously.
Its return value is not a completion result, and a successful transport response does not prove that the script ran successfully.
The script runs after the dispatch returns.
An unhandled Python failure can be surfaced through a native message box rather than the WebSocket result.

Binary inspection suggested that the source runs at top level in a shared `__main__` dictionary.
It also suggested that the loader does not import the script as a module and does not call a function named `run(context)`.
A black-box experiment does not confirm this.
Write scripts that work either way: use explicitly invoked capture functions with local variables and unique output paths.

`__file__` was absent in the first probe.
That probe produced no completion file until its output path was made absolute.
Use absolute input and output paths rather than deriving paths from `__file__` or assuming the process working directory.
Capture exceptions into an explicit report and require that report before interpreting a dispatch as complete.

The successful probe recorded:

```json
{
  "fusion_version": "2706.1.17",
  "documents": 0,
  "active_document": false,
  "status": "application_api_reached"
}
```

The local evidence is `re/Fusion/LocalOracle/ProbeResult.json`.
The following allocation capture created a disposable parametric design, exported four states, and closed that design without saving it to the user's documents.
Its `finally` path restores the original document if one existed and remained valid.
The initial session had no open documents.

## Metadata schema commands

Use the ordinary in-process API `adsk.core.Application.get().executeTextCommand(...)` after the script has reached Fusion.
The following exact command spelling succeeded:

```text
Document.DumpAcitveDocSchema "/absolute/path/to/ParameterSchema.xml"
```

The transposed letters in `Acitve` are part of the registered name.
Correcting the spelling to `Active` changes the command.

The capture returned a success message identifying the requested path and produced a 103,248-byte UTF-16 XML document.
Its root was `MetaTypes`, with 155 immediate metatype records.
Each record carried attributes including `Name`, `_ID`, `_Version`, `_BaseID`, `_AddInMod`, `_Derived`, `_InternalType`, and `_Valid`.
Member-set information was text within the record, not a complete machine-readable wire layout.

For example, `ParameterTableMetaType` had identifier `B0556F58-EE09-46A7-B18F-E296F48E5B13`, version `4`, add-in `CommonData`, and these five registered members:

```text
bIsStateChangedByUser expandedNodeSet groupOrder highWaterMark rParameterSearchByNameHelper
```

This confirms native names and inheritance metadata for types encountered by this document.
It does not by itself determine field widths, wire offsets, custom serializers, uninstantiated feature classes, or ASM body encoding.

The local evidence is under `re/Fusion/LocalOracle/Allocation/`: `Capture.json`, `ParameterSchema.xml`, `empty.f3d`, `two_parameters.f3d`, `deleted_first.f3d`, and `added_third.f3d`.
The report records archive digests, parameter names, expressions, values, units, and timeline counts.
Those archives are vendor-authored controls, not independently generated acceptance candidates.

No other schema command was tested.
A schema dump is not a full entity-graph export.

## Segment stream export

`Segment.Save "/absolute/path/to/Design.xml"` writes to the exact supplied filename.
The filename extension does not choose the format.
An observed invocation returned `Ok` but wrote a ZIP archive containing `BulkStream.dat` and `MetaStream.dat`, despite the `.xml` suffix.

### XML option and failed capture

The exact option command is:

```text
Options.BinaryPersistence
Options.BinaryPersistence /off
Options.BinaryPersistence /on
```

With no flags it reads the setting and returns `Binary Persistence is on` or `Binary Persistence is off`.
`/off` selects XML persistence; `/on` selects binary persistence.

The attempted XML capture switched this setting off and called `Segment.Save`, with restoration planned in `finally`.
The native call crashed before producing the requested XML or the completion report.
Python's `finally` did not establish restoration after this native failure.
After process recovery, [Restore.json](../../../re/Fusion/LocalOracle/Restore.json) confirmed binary persistence was on and zero documents were open.
This sequence is therefore a failed research experiment, not a validated XML export recipe.
Any subsequent controlled attempt must account for process failure and verify the prior option state after recovery; `try/finally` alone is insufficient.
Do not assume the initial state is on or pass both flags.

Whether the option persists across sessions was not tested.
Do not describe the change as memory-only.

Only the binary output was observed.
The XML capture failed, so its output structure is unknown.

### Selecting the segment

How `Segment.Save` chooses its segment is not confirmed by a black-box experiment.
Do not assume that it uses the visible document.
Keep the oracle's disposable document ownership explicit and inspect exported entity content before attributing a capture to it.
Creating a new document is not enough evidence on its own.
Do not clear or replace a user's native selection to steer the command.

Treat `Segment.Save` as a capture operation on disposable documents, not as a read-only inspection command.
`Segment.Load` was not needed for these captures.

Before the failed XML attempt, an earlier failed probe had left a native error dialog pending.
A previously saved segment's disposable document had also been closed.
These are investigative leads, not established crash causes.

## Other recovered diagnostics

`PAsset.EntityIds` was subsequently captured in `re/Fusion/LocalOracle/Inspection/Inspection.json`.
It returned 203 entity references in segment `11`, including 13 named roots, from the disposable two-parameter design.
Each JSON reference had `segId`, `entityId`, and `rootId` fields.
The same report recorded successful `computeAll()` and the binary `Segment.Save` result.

### Entity properties and session identities

The following query succeeded after a later import of the controlled archive:

```text
PEntity.Properties 203
```

`re/Fusion/LocalOracle/Inspection/Values.json` records parameter properties including `userName`, `expression`, `value`, `unit`, `comment`, `creationIndex`, and inherited `rParent` and `rClientObject` references.
The response identified interface `Ns::Parameters::Parameter` and runtime segment `18`.
The parameter value was `1.9000000000000001`, with expression `19 mm` and user name `betaLength`.

The earlier `segId` value `11` could not be reused: a JSON entity reference containing that stale segment ID failed with `Invalid entity ref`.
These runtime segment identities are not portable identities from the F3D archive.
Resolve them from the current import's `PAsset.EntityIds`, or use the simple entity identifier while the intended asset is active.
Do not carry a numeric `segId` between imports or application sessions.

The later feature capture also rejected the raw JSON reference syntax with current segment IDs.
Consequently, the earlier old-segment failure cannot be attributed solely to stale segment identity.
The successful feature graph export uses positive numeric entity IDs in the active import and explicitly skips named roots.
See `re/Fusion/LocalOracle/Features/GraphCapture.json`: 211, 243, and 243 property records, no numeric-query errors, and 14, 15, and 15 skipped roots.
JSON-reference syntax has not been established as a working command input by these experiments.

`Entity.Dump 203` also succeeded but returned a short inheritance and reference-presence description, not the complete member values.

The simple parameter query is verified.
Optional flags of `PEntity.Properties` were not tested.

### Schema introspection limits

The parameter response is useful semantic evidence, but success does not establish that every persistent member of every class is represented.
The schema XML command emits member names, not member types or wire order.
No richer text-command schema interface was established by these captures.

The runtime reflection captures in `re/Fusion/LocalOracle/Reflection` came from a research bridge.
The bridge was removed at the tip and remains in git history.
The [first capture](../../../re/Fusion/LocalOracle/Reflection/Capture.json) reports 1,958 registered types and zero documents before and after the export.
Of 1,916 unique entity/value member sets, 260 were initialized and exposed 938 fields; uninitialized sets retain null members.
Null and uninitialized member sets must remain distinguishable from a known empty schema.

The [version capture](../../../re/Fusion/LocalOracle/Reflection/VersionsCapture.json) succeeded with zero documents before and after export.
Its 3,563 bounded lookups returned 494 initialized sets, 1,428 uninitialized sets, and 1,641 absent entries.
Six classes exposed both an older initialized version and their current one.
An absent lookup does not mean that version never existed.
Only the requested own set has a known lookup version; inherited sets are labeled unresolved.
See the [observed field differences](../../../re/Fusion/LocalOracle/Reflection/VersionDifferences.json).

A generic persistence schema still requires registered definitions, inherited ordering, option meanings, version migrations, custom serializers, and actual load/save callbacks.

### MCP preference

The Fusion MCP server was not needed for the working bridge.
The observed local server endpoint was not listening.
No MCP preference change is part of the bootstrap described here.

## Verification boundary

The verified results are the native Python probe, the disposable parameter allocation archives and the active-document schema dump.
The other verified results are entity-reference enumeration, one parameter property query, its short entity dump, and the binary segment capture.
The XML segment capture failed; its output structure is unknown.
Commands without a capture report are not described here.
No local automated test suite was executed to produce this reference.
Independent reader/writer output still requires complete semantic comparison and vendor-loadability evidence under the repository's acceptance rules.
