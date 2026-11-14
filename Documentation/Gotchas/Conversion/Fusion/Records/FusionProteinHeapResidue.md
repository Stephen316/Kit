# Fusion protein assets carry account data in heap residue

## Expectation

A saved Fusion design holds design data, material data and a few document identifiers. A privacy scan of the outer `.f3d` members should find any account data in the file.

## Actual behavior

Fusion stores material and appearance assets as `ProteinAsset.*.protein` members. Each of those members is itself a deflated ZIP archive. Its `AssetData/InstanceProperties.bin` and `AssetData/DefinitionIteratorProperties.bin` members contain byte ranges that Fusion fills from uninitialized heap memory.

That residue holds fragments of Fusion's telemetry and session JSON from the saving machine. The fragments included hub ids, hashed hub ids, space collection ids, user ids, file ids and session ids. The fragments also included owner display names, cloud lineage URNs and home directory paths. Many fragments start in the middle of a key or a value. Others repeat part of a value with no key at all. A scan for complete `"key":"value"` pairs misses them.

Kit's readers do not decode the residue. `ReadDocument` models did not change when the residue was replaced, and `ReadFusionDoc` documents changed only in the whole-archive digest and passthrough payload.

The census of the 366 Fusion archives that the native I/O work added found residue in 77 of them. Every affected byte was inside a nested protein ZIP.

| Nested member | Members with residue |
| --- | --- |
| `AssetData/InstanceProperties.bin` | 63 |
| `AssetData/DefinitionIteratorProperties.bin` | 42 |

No outer member held account data. A scan that reads only outer members, or that searches compressed bytes, finds none of it.

Both property members are block stores. A 16-byte header is followed by 136-byte blocks, and each block's 8-byte header records how many of its 128 capacity bytes are used. The residue sits in the unused capacity after those bytes. Writing a block's header and used bytes cuts the heap text at the start of that unused capacity. A fragment can therefore begin with only the last two characters of a key, as in `Id": "`. A fragment can also begin with no key at all, as in `": "`.

## Workaround

Recurse into every nested ZIP and scan the decompressed member bytes. Treat a value after an account key, a key tail or an owner marker as private. In each block's unused capacity, also treat a value after any key suffix of two or more characters as private. Also treat an id-shaped value after a bare `": "` at the start of that capacity as private. A truncated value can also start right after heap bytes and end just before the next account key. An example is `…9",` followed by `"hubIdHashed":`. Treat that value as private too when it holds a digit and only id characters. A hex tail of a hashed hub id can also sit glued to a material path. An example is `Mats/Generic/generic.png`, then hex digits, then `",` and `"spaceCollectionId":`. Take only the hex run in that case. A whole quoted value can also follow heap bytes, and the next key can end with the member before its closing quote. Treat that value as private when it holds a digit. Learn a value from these rules only when it has one of two forms. The first form is a hex run of ten or more digits. The second form is a whole quoted value that mixes letters and digits. Residue can also copy a document id from another open document next to an account key. Kit files write the same id in their design streams, so search for fragments only in protein `AssetData` members. Otherwise a plain word such as `Identity` or a material path becomes a search fragment and rewrites every archive. Then search the same run for fragments of each learned value, because truncated copies appear without keys. Keep those searches inside the unused capacity so that no used byte changes. Archives saved from the same account in other corpora carry the same values. A fragment that has no key in one archive can have its key in another. Scan all of them in one run so that a value learned in one archive is found in the others.

Run [`ScrubSaved.py`](../../../../../re/Fusion/LocalOracle/ScrubSaved.py) on Fusion-saved archives before committing them. It replaces account values, display names, home directory names and cloud ids with same-length placeholders. It recompresses only the changed members and keeps member order, names, compression methods, timestamps, attributes, extra fields and comments. Record the saved and committed digests in the scrub ledger. Update every report that cites the saved digest or size. The ledger also lists the written placeholders, and the scrubber leaves values inside them unchanged, so a second run over a scrubbed archive changes nothing.

## Evidence

- [Scrub ledger](../../../../../re/Fusion/LocalOracle/ScrubLedger.json)
- [Scrubber](../../../../../re/Fusion/LocalOracle/ScrubSaved.py)
- [Fixture scrub change entry](../../../../Changes/Fusion/Privacy/FusionFixtureScrub.md)
- [Scrub rule change entry](../../../../Changes/Fusion/Privacy/FusionScrubRules.md)
- [Study corpus scrub change entry](../../../../Changes/Fusion/Privacy/FusionStudyScrub.md)
- [Material store padding](../FusionMaterialStorePadding.md)
