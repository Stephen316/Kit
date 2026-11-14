# Decode pinned Fusion research inputs

## Purpose and prerequisites

Decode committed F3D/F3Z assets with separate typed documents, evidence receipts, and a run summary.
Use Python 3.14 and a trusted checkout containing the pinned corpus Git objects.
Choose an unused output directory and asset paths from `re/automation/Corpus.json`.
No CAD application or model provider is required.
The [step register](AutomationSteps.md) owns implementation and qualification status.

## Procedure

Run the reader from the selected checkout:

```sh
uv run --frozen --no-default-groups --extra dev --python 3.14 python re/automation/FusionReader.py --root . --asset re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d --output /tmp/KitFusionResearch
```

Repeat `--asset` for up to 1000 distinct committed inputs.
The direct entry point remains `re/automation/FusionReader.py` with the same reader options.
Use `--manifest PATH` for another supported manifest.
`--allow-partial` explicitly permits strict-first fallback and records any strict rejection.

## Expected result and limits

`summary.json` records every selected asset as decoded, rejected, or reader error.
Each decoded asset has a path-hash directory containing `document.json` and `receipt.json`.
Documents retain SDK serialization and pass typed reconstruction.
Receipts bind source bytes, SDK/tool fingerprints, options, hashes, and unresolved evidence.

Exit `0` means all selected assets decoded.
Exit `3` means a published summary includes rejected or reader-error outcomes.
Exit `1` means the run failed before normal publication.
Existing output directories and symlinks are refused.
Files use `0600` and directories use `0700` where supported.

Inputs are bounded to 256 MiB, neutral JSON to 64 MiB, receipts to 32 MiB, and a run to 4 GiB.
Pin checks cover path, blob, size, SHA-256, and prefix.
SDK source changes detected during decoding reject publication.
`portable_complete` remains false, and native acceptance remains not established.
Both strict and partial research outputs carry `kit.research_read_status = unqualified` in document metadata. The public reader can open them for inspection. Public writing and conversion reject marked files before staging a destination. Regenerate older research artifacts to attach the marker.
Structural decoding and partial fallback do not qualify editable cross-format conversion.

## Recovery and related information

Fetch missing pinned commits, restore the intended manifest, or choose another output path.
Inspect per-asset reasons and implement missing codec knowledge instead of relaxing checks.

- [Separate installed CLI proposal](https://github.com/TryUniCAD/Kit/pull/119)
- [Reader source](../../../re/automation/FusionReader.py)
- [SOLIDWORKS reader](SolidworksResearchReader.md)
