# Decode pinned SOLIDWORKS research inputs

## Purpose

Use this command to inspect a pinned SLDPRT through the existing SDK reader.
It writes the existing `CadDocument` JSON and a separate research receipt.
Use the [step register](AutomationSteps.md) for current implementation and qualification status.

The command preserves what the reader returns.
It does not establish complete portable semantics, fix mappings or qualify a native conversion.
It never launches CAD applications or models.

## Before you start

Use Python 3.11 or later, Git and a complete repository checkout containing the pinned corpus commit.
Install the locked environment with `uv sync --frozen --no-default-groups`.
The command imports this checkout's `src/` tree explicitly.
No CAD installation, model credential or network connection is required after setup.

Run from the repository root.
Choose an unused output directory outside the input corpus.
The example path `/tmp/KitReadExample` is user-selected and must not already exist.

## Procedure

1. Select an SLDPRT path from [the corpus manifest](../../../re/automation/Corpus.json).
2. Decode its committed bytes:

   ```shell
   uv run --frozen python re/automation/SolidworksReader.py --asset re/solidworks/examples/.SLDPRT/example.SLDPRT --output /tmp/KitReadExample
   ```

3. Inspect `receipt.json` before using `document.json` in further research.
4. Keep unresolved entries and independent source requirements with the document.

Use `--configuration NAME` to select an existing configuration.
The name has a 256-character limit.
Use `--manifest PATH` for another version-1 corpus manifest.
`--root` must identify this reader's SDK checkout.

## Expected result

Exit code `0` means the SDK decoded the file and its JSON survived typed reconstruction and reference validation.
The command prints the output path, fingerprint, document hash and evidence counts.
It always reports `portable_complete: false`.
Independent semantic qualification and native acceptance remain unavailable.

| File            | Content                                                                                          |
| --------------- | ------------------------------------------------------------------------------------------------ |
| `document.json` | Unchanged SDK `CadDocument` serialization, including retained native evidence                    |
| `receipt.json`  | Exact source identity, decoder inputs, output hash, field paths, records and unresolved findings |

Output directories use mode `0700`, and files use `0600` where the operating system supports these permissions.
The receipt is published last.
Treat a directory without its receipt as incomplete after an interrupted process.
Preserve incomplete artifacts for diagnosis and select a new output path for the next attempt.
The command refuses an existing directory or symlink.

## Evidence contract

The receipt records the corpus revision, manifest hash, path, Git blob, source hash, size and prefix.
The selected path must resolve to that blob in the pinned Git tree.
The command reads committed bytes rather than the working copy.
It checks actual size, SHA-256 and prefix before decoding.
SLDASM, other formats and embedded Kit documents are rejected.
This command checks the selected asset, not the entire manifest or independent authorship.

The receipt also records the SDK revision, a digest of Python source hashes, research tool hashes, Python version and options.
Source changes detected during decoding reject the attempt.
Inputs are limited to 256 MiB, neutral JSON to 64 MiB and receipts to 32 MiB.
The evidence walk has a 200,000-entry bound.

Field paths are JSON pointers into the serialized document, including `$tuple` and enum wrappers.
Records are `typed_unverified`, `partially_interpreted` or `native_only`.
Inherited provenance identifies an enclosing record, not a proven byte location for each field.
Absent provenance remains unavailable.
Numeric confidence does not qualify a field.

Unresolved entries include native-only definitions, retained bytes, `native:` codes and reader diagnostics.
Extrusion and revolution direction, frame and operation remain explicitly unqualified.
Every receipt retains the missing independent source-inventory and acceptance requirement.
Fields omitted by the existing reader cannot be discovered solely from its output.
Consequently, the receipt reports byte accounting as unavailable and never claims a complete unresolved-byte census.

Retained native bytes are research evidence and can contain the source design.
They are not portable design semantics or an authorized writer template.
See [the replay-evidence gotcha](../../Gotchas/Research/ReaderReplayIsNotPortableSemantics.md).

## If the command fails

Exit code `1` reports a bounded JSON error on standard error.
Missing Git objects require the pinned commit to be fetched.
Digest, prefix or blob mismatches require the intended manifest and source revision to be restored or reviewed.
Unsupported records and model-validation failures require decoder research rather than relaxed checks.
An existing destination requires a different output path.
No successful receipt is written for a rejected attempt.

## Verification boundaries

Remote process coverage exercises actual pinned files, typed reconstruction, tamper rejection and overwrite refusal.
The corpus scenario records decoded and rejected outcomes for all 58 pinned parts without interpreting rejection as support.
These checks run in the existing workflow-quality job.
No local tests or CAD experiments ran for this implementation.
Use the step register and PR comments for exact-revision results.
Rendered usability and full language conformance remain unverified.

## Related information

- [Reader source](../../../re/automation/SolidworksReader.py)
- [Evidence census](../../../re/automation/ReaderEvidence.py)
- [Neutral contract audit](NeutralContractAudit.md)
- [Pinned corpus](PinnedCorpus.md)
- [Parallel sessions](ParallelSessions.md)
