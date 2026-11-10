<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Study evidence and live capture protocol

[Fusion feature index](../README.md)

Study scripts, reports and capture paths in this note are relative to [the Study directory](../Study/README.md).

The [UniCAD Fusion notes](../README.md) describe the SDK reader and the import.
The original standalone checkout was recorded at:

```text
/Users/stephenh/.codex/visualizations/2026/10/17/01a14ba1-a51c-7f72-b92e-9f1f0114012e/FusionFileStudy
```

## Run the reader

Use Python 3 with its standard library. Older Python ZIP implementations need `libzstd` for the archives' compression method 93. On the machine used for this study:

```sh
FUSION_STUDY_ZSTD='/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production/c139e2731e42a0340acc3d34de2cbdb01237a27c/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'
/usr/bin/python3 decode_basics.py --zstd-library "$FUSION_STUDY_ZSTD" profiles-66b0447c28ac/concentric_annulus.f3d > decoded.json
```

Run this from the study directory. Supply a different `libzstd` path if Fusion is installed elsewhere. The flag can be omitted when the Python ZIP implementation supports Zstandard or a system `libzstd` is discoverable. Decoding existing files does not require running Fusion.

The main entry point is `decode_basics.decode_basics(path, zstd_library=None, *, include_asm_attributes=False)`. The parameter-only entry point is `decode_parameters.decode_file`. Both read archives without extracting members onto disk.

## Evidence and navigation

The study distinguishes stored data, derivations and open questions.

- **Observed** fields or caches are present in the saved bytes. Structural
  checks establish record bounds, identities and ownership.
- **Derived** values are computed from the decoded inputs. Where reported, an independent cache or Fusion API comparison corroborates
  the derivation for the cited captures.
- **Unresolved** fields or relationships lack a supported interpretation for
  the stated scope. Preserve the bytes and record the limit of the finding.

Keep archive members, native class names and JSON keys in code spans. Use
`BODY`, `FACE`, `LOOP` and `EDGE` for ASM record kinds and B-rep for the
boundary representation. Distinguish native object IDs from ASM indices.
State the coordinate frame and units for measurements. For field maps, give
the byte offset, width and type separately, as in the
[SOLIDWORKS field maps](../../solidworks/records/Definition.md#2-the-preamble).

- `fusion-class-catalog.json` catalogs opaque class GUIDs, namespaces, base classes, and meanings observed across the local corpus. Type numbers vary between files; they are not universal feature IDs.
- `*-decoding.json` files are stage-specific evidence snapshots with focused comparisons. Historical snapshots can describe an item as unsupported that a later stage implements. Run the reader for current output.
- Generated sample folders contain `.f3d` archives and `ground_truth.json` captured through Fusion's API. Generator scripts use new documents, export locally, and close only their own documents without saving to the cloud.
- Generator scripts require execution inside Fusion's Python environment. They are not ordinary terminal scripts. Existing archives are sufficient to use the decoder.

The metadata index validates object/header identities, registered primary classes, and continuation inheritance. Field meanings are still inferred from a limited corpus; a validated record boundary does not prove that every field in the record is understood.

## Continue the research

Follow the repository's [agent guidance](../../../AGENTS.md) when extending the
study. Commit verified stages locally and record partial coverage at the level
the saved examples support.

Use small controlled API examples, vary one setting where practical, and retain unknown fields. Prefer metadata/class identities and explicit references over byte searches or inference from geometry alone.

### Live capture protocol

Live capture requires explicit user authorization and a verified repair to
the Trim cleanup order. Suspend capture on process loss or an unsafe
transaction. While the capture hold is active, the dispatcher blocks before
UI or event access except for an explicitly authorized validation whose
entry-point and helper hashes match the reviewed sources. Saved-file decoding
runs independently.

`fusion-live-capture-hold.json` records the authorization and native validation
evidence. Five healthy captures completed and closed in the same process,
including two subsequent sketch-Line contrasts. The evidence verifies the
observed capture lifecycle.

`fusion-capture-repair-status.json` retains the original Trim validation, the
Line captures and the corrected Rule surface capture. After the user unlocked
Fusion, targeted command access succeeded. Two complete Rule cases created
16 face witnesses and four archives, then closed both owned documents cleanly.
The same Fusion process (PID 5619) stayed alive, with no newer local CER crash
archive. The earlier locked-session observation and recovered pre-add witness
failure have separate timestamps.

`dispatch_fusion_script.py` runs an owned `Generate*.py` script through the known Fusion text-command field using macOS accessibility and Return events posted only to the Fusion process. It checks existing event-posting permission and verifies the command field before posting; it never requests permissions or posts global keyboard events. Actual generator output is required to prove execution. The Loft capture and initial Sweep pass executed while other applications remained foreground. Generators must run serially.
