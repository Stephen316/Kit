# FreeCAD extrusion direction and reversal

Supported inline extrusion writes now retain the normalized base `Dir` independently of the saved `Reversed` property.
An explicit positive direction with `reversed=True` no longer silently emits an unreversed operation.
Implicit profile normals are emitted without pre-reversing them, so the native flag applies reversal exactly once.
Negative profile normals and negative explicit axes retain their original sign before the flag is applied.

This follows the [official FreeCAD 1.0.2 parameter computation](https://github.com/FreeCAD/FreeCAD/blob/1.0.2/src/Mod/Part/App/FeatureExtrusion.cpp#L199-L237): the application selects the base direction, normalizes it and then applies the independent `Reversed` property.
Symmetry remains a separate total-thickness control.
The earlier [native read repair](FreeCadNativeEndSemantics.md) preserves the same properties when reading a native-only archive.

`AddExtToolMut` accepts a backward-compatible keyword-only `Reversed=False` argument.
Ordinary inline emission supplies the definition's reversal flag, retaining the existing `direction_multiplier` or Cut fallback when that definition flag is absent.
An explicit false definition still takes precedence over those fallbacks.
The three linked-edit seed callers retain their existing effective direction vectors and default false flag: `HasEditExtMut`, `AddBodySeedMut` and `AddScaleSeedMut`.
No linked-feature, reconciliation, native-semantic or carrier admission is expanded.

## Process coverage and evidence

The new process coverage reuses the independently authored rectangle and end-owner fixtures from the existing two-length binding checks.
It sends fresh typed documents through the real portable codec and public `WriteDocument` boundary with carriers disabled.
Ten cases combine explicit and implicit directions, positive and negative axes, independent reverse flags and symmetric total thickness.
Explicit vectors also exercise normalization.
Each case checks actual `Document.xml` direction and reversal properties, both distance properties, symmetry and the existing spreadsheet dependencies.

An independent public native read removes only the ZIP neutral manifest and the three XML manifest properties from the generated archive.
All other native records and archive entries are retained.
That read checks the saved raw direction and flags rather than the original portable snapshot.
The process reports remain property observations; native application acceptance is unestablished.

Pinned formatting, source syntax, type, steering, path, rationale, binary-range and whitespace checks validate this change statically.
No local tests, collection, reproductions, SDK or CLI execution, generators or CAD application runs were performed.
Hosted process checks and independent FreeCAD edits, rebuild, save and fresh reopen remain required.
