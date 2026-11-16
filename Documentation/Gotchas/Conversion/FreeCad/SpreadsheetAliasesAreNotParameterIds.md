# Spreadsheet aliases are not typed parameter IDs

The earlier native reader preserved `Parameters.alias` expression text but did not create typed parameters for actual spreadsheet cells.
Its expression records therefore had empty `parameter_ids` even when the saved sheet declared both depth drivers.
The model-free Fusion workbook reconciler uses a separate qualified binding and cannot resolve native extrusion sheets.
This is separate from choosing an embedded snapshot over native edits and from native body inventory.

Resolve a supported direct reference through the actual sheet object name and its unique native alias/cell address.
Do not use a display label, equal numeric values, row order or Kit's alias metadata to guess ownership.
FreeCAD persists a cell's `content` and `alias`, and the sheet's `Cells Count` controls how many records its restore consumes.
The bounded recovery therefore requires the actual count to agree and refuses ambiguous sheets as a whole.
It also requires external-link records to be unique and empty; unknown group children cannot silently disappear from dependency scope.
Unsupported references and cells retain raw metadata and text with an explicit unresolved diagnostic.

A syntactically valid alias is not proof that its current saved property agrees with the literal cell or that native geometry was recomputed.
The [recovery](../../../Changes/FreeCad/FreeCadNativeSheetAliases.md) preserves both values and requires quantity corroboration before linking.
Its stale control is independently authored XML; the earlier operator's saved copies were restored before saving and do not establish a discrepant native-save witness.
Native fallback and replay verification must both recover aliases before computing semantic equality, or an unchanged native file can lose exact replay solely because the reconstructed dependency graph differs.
Local checks were static; process and native acceptance evidence remain distinct.
