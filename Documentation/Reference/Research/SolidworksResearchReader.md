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
Its `document.json` also carries `kit.research_read_status = unqualified` in document metadata. The public reader can open that file for inspection. Public writing and conversion reject it before staging a destination, even when the side receipt is absent. Regenerate older research artifacts to attach the marker.
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

SOLIDWORKS part equations retain their source text and link quoted references to known global variables or exact, unique `dimension@feature` names. The receipt reports missing or ambiguous right-hand references as `unresolved_equation_reference`.

The public write and conversion APIs reject parts that carry these unresolved equation references, including when exporting to interchange JSON. The research reader's evidence files remain available for inspecting those parts.

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

### Discovery census

On a completed **Workflow quality** run, download the `SolidworksDiscoveryCensus-<attempt>` artifact. It contains `SolidworksDiscoveryCensus.json` for all 25 native parts in the P01, P03 and P04 discovery families. The census uses the tested revision's Git objects and verifies each capture against the original exact receipt hash. Its alternate reader manifest binds the path, blob, byte count, SHA-256 and prefix. The historical 58-part reader check continues to use the pinned corpus manifest.

The `boundary` field records whether the low-level native model and the process-based research reader each decoded a part. A native decode followed by a reader rejection localizes the failure to the later reader boundary. On successful reads, the report gives separate native and neutral comparisons to the measured file, including dimensions, equation text and bindings, operation codes, world-space sketch segments and observed support. Inspect the underlying records when a diagnostic comparison differs. Names and counts in the report serve this fixture census and do not establish semantic identity across formats.

The census uses mass and centroid values from the saved independent measurements. For the two Front Plane P03 direction cases, it derives expected Z bounds from the measured centroid and blind-boss depth. It checks both P04 cut-centering equation bindings against each saved part's measured source. Other semantic mismatches and decoder rejections appear as research findings unless they affect a required check. Unverifiable inputs and invalid reader receipts fail the census. Use [the change entry](../../Changes/Research/SolidWorksDiscoveryCensus.md) for scope and evidence.

The P04 termination check uses the same measured receipts. It requires ten matching blind cut depths and one native through-all code with no authored depth. The neutral reader preserves the through-all code on its native fallback. Typed through-all projection remains open.

The inch-length check verifies seven named, feature-owned resolved dimensions and three blind depths in the inch variants. Display metadata identifies the source unit and its native property stream. P04's six sketch dimensions remain outside this check while their configuration-stream ownership is unresolved. [Resolved-feature inch lengths](../../Changes/Research/SolidWorksResolvedInchLengths.md)

The native reader [indexes inch scalar names per owner](../../Changes/Research/Readers/IndexedInchScalarBinding.md) across direct and linked-child binding.
Duplicate-name candidates retain the existing unresolved status.

The census also retains [principal support-layout candidates](../../Changes/Research/PrincipalSupportEvidence.md) with hashed native spans and explicit unresolved ownership.
Its support-evidence gate checks 25 measured plane identifiers, including three YZ variants.
These candidates do not change production support decoding or establish semantic qualification.

[Direct adapter writes](../../Changes/Research/DirectAdapterWriteSafeguards.md) apply the registry's research, inch-length and equation safeguards before output mutation.
The [support write gate](../../Changes/Research/SolidWorksSupportWriteGate.md) also rejects native-derived sketches with fallback, missing or unframed support evidence.
Native reading and manual serialization remain available for inspection.

### Historical corpus

Remote process coverage exercises actual pinned files, typed reconstruction, tamper rejection and overwrite refusal.
The corpus scenario requires every one of the 58 pinned parts to decode and reconstruct successfully.
Any individual rejection fails that gate rather than passing through an aggregate success threshold.
Four concurrent CLI processes bound execution overhead without changing the expected outcomes.
This requirement covers the existing research projection, not independent semantic qualification.
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

Unresolved equation and inch-dimension markers block public and direct interchange writes even after the source format is relabeled. See [retained semantic markers](../../Changes/Research/ReidentifiedWriteMarkers.md).
