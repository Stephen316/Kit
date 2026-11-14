# Pinned Fusion reader integration

## Behavior

A05 adds a research command around the existing SDK Fusion reader.
It verifies each selected pinned Git asset before decoding and reads committed bytes only.
It preserves the SDK neutral JSON and writes a separate evidence receipt for each decoded file.
A run summary records one outcome for every selected file: decoded, rejected or reader error.

The command uses the strict reader first.
With `--allow-partial`, a strict rejection starts the partial legacy reader for that file.
Partial receipts record the strict rejection reason and an explicit unresolved entry.
The receipts reuse the SOLIDWORKS reader's evidence census.
Typed reconstruction does not establish independent semantic or native acceptance.

One process can decode up to 1,000 files.
This matches the grouped small-file sessions in the [parallel-session design](../../Reference/Research/ParallelSessions.md).

## Usage and limits

Follow [the reader guide](../../Reference/Research/FusionResearchReader.md).
Use Python 3.14, pinned F3D or F3Z paths and an unused output directory.
No model or CAD installation is required.
The command does not select a native history in a multiple-history archive.
Partial results are research evidence and the qualified Fusion writer does not accept them.
Unknown semantics remain research work rather than inferred successful decoding.
See [the retained-evidence gotcha](../../Gotchas/Research/ReaderReplayIsNotPortableSemantics.md).

## Verification

Source inspection, Python 3.14 syntax, formatting, linting, strict static typing and repository steering checks of the new process coverage passed before publication.
No local tests, test collection, CAD experiments or model calls ran.
Remote process scenarios cover the strict control file, F3Z rejection, tampered pins, invalid selections, overwrite refusal and all 714 pinned Fusion files.
The corpus scenario prints the outcome census.
It does not yet require an exact outcome for each file.
Exact-revision results are recorded in the step register and PR comments after CI completes.
Full semantic qualification, native acceptance, rendered usability and full language conformance remain unverified.
