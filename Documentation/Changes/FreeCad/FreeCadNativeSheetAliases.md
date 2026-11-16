# Native spreadsheet alias dependencies

Native-only FreeCAD reads now recover a bounded set of typed spreadsheet-cell parameters and direct property dependencies.
The reader uses actual `Spreadsheet::Sheet` object names, unique cell addresses and aliases, and current literal cell contents.
It preserves the native property parameter IDs, feature/end owners, values and units, expression source text and language, raw native metadata, source bytes and source SHA-256.
The native fallback and unchanged-native replay verification apply the same recovery before semantic digest comparison.
Embedded-manifest reconciliation and body geometry inventory remain separate paths.

The supported reference is a direct `ObjectName.alias` expression with an optional leading `=`.
Supported names begin with an ASCII letter and contain only letters, digits or underscores, with at most 128 characters.
Aliases that resemble cell addresses or reserved units/constants remain unresolved.
Cell contents must be finite decimal literals, optionally beginning with `=`, with an explicit recognized length or angle unit, or no unit for a dimensionless number.
Length units are mm, cm, m, in and ft; angle units are rad and deg.
The stored cell spelling determines its typed unit and kind.
The reader requires dimensional and numeric corroboration with the current saved native property through the existing quantity comparison before assigning a dependency ID.
A literal/property mismatch retains both observations and the original expression without a guessed target, with an explicit diagnostic.
This does not prove that a native recompute occurred or that geometry is current.

Duplicate addresses, aliases or sheet names cannot select an arbitrary row.
Cell groups may have one empty `XLinks` record with count zero; external links, duplicate link records and unknown group children leave the sheet unresolved.
Unsupported formulas, arithmetic, label-qualified or external references, unknown units and missing aliases retain their raw native representation and unresolved expression text with `freecad.sheet_alias.unresolved` diagnostics.
Kit's `ParameterAliasesJSON` metadata is not alias authority.
The bounded recovery admits at most 16,384 native object records, 64 sheets, 4,096 total cells and 16,384 existing parameters.
Literal text is limited to 256 characters, mantissa digit runs to 64 digits and exponent magnitude to 308 with at most three digits; nonfinite and underflowed quantities are rejected before linking.
Expression text is limited to 1,024 characters.
An exceeded recovery budget preserves the original native document and reports the unresolved limit instead of accepting a partial alias prefix.

Source-authored public process coverage reads native XML without either Kit manifest representation.
It checks independently owned forward/reverse depths, equal values with reordered cells, edited matching values, mm/cm conversion, dimensionless values, label and metadata decoys, stale observations, ambiguous cells, unsupported syntax/units and recovery limits.
It also requires byte-identical public unchanged-native replay.
Local verification is static only; hosted process execution remains required.
The operator's [physical native readback](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6930111667) established the earlier text-only dependency gap, not a retained discrepant-edit save control.
No native acceptance or broader conversion admission is established by this recovery.

The vocabulary follows FreeCAD 1.0.2's [sheet persistence and alias checks](https://github.com/FreeCAD/FreeCAD/blob/1.0.2/src/Mod/Spreadsheet/App/PropertySheet.cpp) and [cell content/alias persistence](https://github.com/FreeCAD/FreeCAD/blob/1.0.2/src/Mod/Spreadsheet/App/Cell.cpp).
See the [alias gotcha](../../Gotchas/Conversion/FreeCad/SpreadsheetAliasesAreNotParameterIds.md).
