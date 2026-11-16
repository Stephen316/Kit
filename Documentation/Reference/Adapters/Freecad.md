# FreeCAD adapter

## Purpose and scope

The `freecad.fcstd` adapter handles `.FCStd` files through direct archive parsing and writing.
Production conversion does not require a FreeCAD application or module.
Feature coverage depends on the implemented reader and writer families.

## Archive structure

A FreeCAD document is a ZIP archive with `Document.xml` and related resources.
Shape data can reside in `.brp` members.
Mesh data can reside in `.bms` members.
Kit can also store a neutral manifest in `interchange/document.json`.

```mermaid
flowchart LR
    Archive[FCStd archive] --> XML[Document.xml]
    Archive --> Geometry[Geometry resources]
    Archive --> Manifest[Kit manifest]
    XML --> Model[Neutral document]
    Geometry --> Model
    Manifest --> Model
```

An embedded manifest and a native object graph are different representations.
The vendor application does not necessarily interpret the neutral manifest.

## Resource limits

The archive implementation uses these limits:

| Item                   | Limit     |
| ---------------------- | --------- |
| Archive members        | 16,384    |
| Individual member      | 512 MiB   |
| Total expanded members | 1 GiB     |
| `Document.xml`         | 512 MiB   |
| Compression ratio      | 500       |
| External files         | 256       |
| Manifest JSON depth    | 256       |
| XML depth              | 256       |
| XML nodes              | 2,000,000 |

These values use binary byte units.
The archive checks also reject unsafe paths and unsupported entry types.
A limit failure is not permission to disable validation.

## Native interpretation

The native reader maps object declarations, properties, sketches, and feature dependencies into neutral records.
The protocol tables identify recognized type families.
A recognized type identifier does not prove complete reconstruction of every instance.

For native `Part::Extrusion`, the reader preserves the saved `Symmetric` and `Reversed` flags.
Equal forward and reverse distances do not imply symmetry.
Both raw distances and the original direction remain available, including an inactive reverse distance in symmetric mode.
See [native extrusion end semantics](../../Changes/FreeCad/FreeCadNativeEndSemantics.md) for the retained termination convention, native-only process coverage and acceptance limits.

| Component     | Responsibility                                    |
| ------------- | ------------------------------------------------- |
| `Archive.py`  | Archive resources and document representation     |
| `Native.py`   | Native object graph interpretation                |
| `Protocol.py` | Type and property vocabulary                      |
| `Brep.py`     | B-rep handling                                    |
| `Adapter.py`  | Public adapter operations and result construction |

## Write paths

The writer can replay suitable unchanged source data.
For other inputs, it constructs native records for implemented features and retains additional information as required.
Inspect the resulting transfers and usability flags.
Do not infer losslessness from a generated `Document.xml` file.

Public writes now refuse required features that the active emission path cannot express as editable records.
This check runs before destination and component files are created, including when carrier output is enabled.
Standalone edit-plan qualification does not establish the same support for a nested component emission path.
See [native semantic write qualification](../../Changes/Research/Readers/NativeSemanticWriteQualification.md) for the checks, compatibility restriction, and additional in-memory encoding cost.

For supported inline extrusions with two ends, declare ordered forward and reverse owners through `FeatureStep.attributes`:

```python
attributes={"length_parameter_ids": ("depth:forward", "depth:reverse")}
```

Both IDs must occur in the feature's parameter roster and identify distinct driving length parameters owned by that feature.
Their physical values must match the corresponding inline end lengths within an absolute `1e-9` mm, with no relative tolerance.
The writer connects both `LengthFwd` and `LengthRev` to their own spreadsheet expressions.
Equal lengths and a reordered generic parameter roster do not exchange those dependencies.
Supported parameter units are normalized to millimetres for native distance properties.
The spreadsheet retains each parameter's declared units.

A two-ended feature with a parameter roster and missing or invalid end ownership is refused before output publication.
Literal two-ended features without a parameter roster retain literal editable properties.
Symmetric extrusion retains one total-thickness driver.
See [two-length bindings](../../Changes/FreeCad/FreeCadTwoLengthBindings.md) for scope, process coverage and the outstanding native edit, rebuild and fresh-reopen evidence.

Supported inline extrusions emit the normalized profile normal or explicit direction as `Dir` and retain reversal in the independent native `Reversed` property.
The reversal flag applies once, including when an explicit axis is supplied.
An explicit false definition takes precedence over the existing direction-multiplier and Cut fallbacks.
Linked-edit seeds retain their existing effective direction vectors and default false flag.
See [extrusion reversal emission](../../Changes/FreeCad/FreeCadReversedExtrusion.md) for process coverage and the outstanding native acceptance evidence.

The [independent FreeCAD 1.1.4 witness](../../Changes/FreeCad/FreeCadEndNativeWitness.md) observed scoped driving edits, restoration, save and fresh reopen at exact source `b32222b5`.
Its original generated packages had no cached BREP and exposed zero solids before native recompute.
The post-recompute and saved-copy successes do not establish initial geometry availability or broader route qualification.

The `portable` writer option defaults to true in the inspected adapter revision.
For assemblies, portable output can include companion component files.
The final destination identifies the base location for those files.
Keep the output bundle together when moving it.

## Assembly behavior

The adapter maps native assembly objects and links to neutral definitions and instances.
Constraint mappings depend on the implemented native joint representation.
A matching joint name does not establish equal motion or constraint behavior.
Inspect the [assembly model](../Model/Assembly.md) and acceptance evidence.

## Use and recovery

1. Keep the source and destination paths separate.
2. Check the requested feature families before conversion.
3. Inspect the writer's transfer records.
4. Preserve companion outputs with the main file.
5. Obtain the required remote target-application evidence.

If archive validation fails, record the limit or invalid member.
If native output is incomplete, retain the structured failure.
Do not load FreeCAD as a production fallback.

## Sources

- [Adapter](../../../src/convert/adapters/freecad/Adapter.py)
- [Archive validation](../../../src/convert/adapters/freecad/Archive.py)
- [Native interpretation](../../../src/convert/adapters/freecad/Native.py)
- [Protocol tables](../../../src/convert/adapters/freecad/Protocol.py)
- [FreeCAD integration coverage](../../../tests/Convert/Freecad/)
