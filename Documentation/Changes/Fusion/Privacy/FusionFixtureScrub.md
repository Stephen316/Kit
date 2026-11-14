# Scrubbed account residue from saved Fusion fixtures

## Behavior

Seventy-seven Fusion-saved research archives under `re/Fusion/LocalOracle/` were rewritten in place.
Their nested protein asset members carried uninitialized heap bytes with account identifiers, owner display names, home directory names and cloud ids.
Each such value now has a same-length placeholder.
The [protein residue gotcha](../../../Gotchas/Conversion/Fusion/Records/FusionProteinHeapResidue.md) explains the source.

[`ScrubSaved.py`](../../../../re/Fusion/LocalOracle/ScrubSaved.py) performs the rewrite with generic rules and holds no account values.
One run gives each cloud id the same placeholder in every archive.
Only changed members are recompressed.
Member order, names, compression methods, timestamps, attributes, extra fields and comments stay unchanged.

The [scrub ledger](../../../../re/Fusion/LocalOracle/ScrubLedger.json) records each archive's Fusion-saved digest, committed digest and per-rule counts.
Reports, censuses, documentation and test constants that cited a Fusion-saved digest or archive size now cite the committed one.

Research reports and scripts that recorded absolute local paths now use repository-relative paths, `~/` or `$TMPDIR/`.
The reflection capture archive was rebuilt with the same members and relative paths.

## Verification

`ReadDocument` returned equal models for the saved and scrubbed versions of all 64 archives it reads, and their `EmitParsed` round trips stayed equal.
The other 13 archives raised the same error before and after the rewrite.
`ReadFusionDoc` returned equal documents for all 73 archives it reads, apart from the whole-archive digest and passthrough payload.
The other 4 archives raised the same error before and after the rewrite.
The remapped lineage URN received one placeholder in both archives that carry it.
Only nested protein members changed, and every leaf member kept its size.

Static checks ran locally; no local automated tests were run.
