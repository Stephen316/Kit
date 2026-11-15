# `re/` — reverse-engineering workspace

Durable reverse-engineering findings and tooling for native CAD formats. The SOLIDWORKS
workspace described below retains its original structure. The imported
[Fusion study](Fusion/README.md) contains the experimental Fusion decoder, saved
captures and validation evidence, with its source history preserved.

**Start with [`Playbook/README.md`](Playbook/README.md)**, the reverse-engineering instruction book.
Any agent tasked with reverse engineering a format must read it in full first, together with the
[CAD success criteria](../Documentation/Reference/Operations/CadSuccessCriteria.md), which are
mandatory. The book covers file anatomy, loader-DLL analysis with REA, generative corpora authored
through vendor APIs, corpus correlation, writer models, the open-source toolchain, and per-vendor
notes.

`Methodology.md` is the short history of how SOLIDWORKS was cracked; where it and the playbook
differ, the playbook wins. The existing SOLIDWORKS directories provide the worked example both were
distilled from. `Fusion/` preserves a separate native-file study and its original commit history.

## Research inputs

Keep vendor software outside repository checkouts.
CAD files, documents, independently authored tools, and recorded format knowledge belong in this workspace.
Follow the [research artifact policy](../Documentation/Reference/Research/ResearchArtifacts.md).
The [external input guide](binaries/README.md) describes licensed installation verification.

## Layout

| directory     | what is in it                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Playbook/`   | The reverse-engineering instruction book: file anatomy, loader analysis with REA, generative corpora, corpus correlation, writer models, toolchain, techniques, shape catalogue, evidence rules, orchestration, vendor notes and checklists. Read `Playbook/README.md` first.                                                                                                                                                                                                                            |
| `Fusion/`     | Imported experimental Fusion native-file decoder, capture tools, saved examples and audit reports; original source history and evidence bytes preserved. `examples/` holds the sample `.f3d` and `.f3z` files.                                                                                                                                                                                                                                                                                           |
| `catia/`      | `examples/` holds the CATIA V5 `.CATPart` and `.CATProduct` samples. The two directories stay siblings so product reads find their parts.                                                                                                                                                                                                                                                                                                                                                                |
| `binaries/` | External installation manifest and verification helper. See `binaries/README.md`. |
| `solidworks/` | the findings. Layered: `container/` (file framing + the signature table), `archive/` (the `su_CArchive` grammar, the reader's identity, object segmentation), `records/` (per-class field layouts), `features/` (extrude, revolve, sketch, arc, bodies), `corpus/` (what corpora exist and what each proves), `measurements/` (every volume measurement, with controls), `examples/` (the sample part, the V8 corpus and the gitignored `Random/` corpus), `Fixtures/donors/` (extracted donor streams). |
| `tooling/`    | how the work was done and how to redo it: `ghidra/` (headless decompilation), `windbg/` (the cdb runtime trace), `harness/` (the COM measurement loop).                                                                                                                                                                                                                                                                                                                                                  |
| `data/`       | the extracted tables and traced artefacts the findings cite: the 1000-entry signature table, the 2607-class `Serialize` map, the object segmentations, the class vocabulary.                                                                                                                                                                                                                                                                                                                             |

## How to navigate by question

| you want to know                                                    | start at                                                           |
| ------------------------------------------------------------------- | ------------------------------------------------------------------ |
| how to reverse engineer any CAD format, step by step                | `Playbook/README.md`, then the chapter for your phase              |
| how a `.SLDPRT` file is framed, and how to write a valid header     | `solidworks/container/README.md`                                   |
| how objects are tagged inside a stream, and why byte edits renumber | `solidworks/archive/Grammar.md` §2, then `archive/Segmentation.md` |
| what class owns a given byte                                        | `solidworks/records/Serialize.md`, then `data/SerializeMap.json`   |
| whether a specific field is trustworthy                             | the confidence column of the table that declares it — see below    |
| what has been _measured_ rather than inferred                       | `solidworks/measurements/README.md`                                |
| what does not work, and the traps                                   | `solidworks/README.md` "Negative results and traps"                |
| how to reproduce the decompilation                                  | `tooling/ghidra/Setup.md`                                          |
| how to reproduce the runtime trace                                  | `tooling/windbg/README.md`                                         |

## Confidence vocabulary

Every field table in `re/solidworks/` labels each row. The vocabulary is defined in
`solidworks/records/Serialize.md` and used consistently everywhere:

- **confirmed** — read out of the decompiled `Serialize` _and_ the byte arithmetic reproduces a real
  traced object span, a real corpus record, or a measured volume exactly.
- **partial** — read out of the decompiled `Serialize`, but nothing available exercises the field:
  its value is constant across the corpus, or the branch is never taken, so nothing independent
  checks it.
- **not found** (spelled **unresolved** in the oldest tables) — not recovered.

Treat the distinction as load-bearing. A **partial** offset is a hypothesis with an address, not a
fact; several of them turned out to be uninitialised memory rather than parameters.

## Reproducing

Everything here was produced on Windows with PowerShell, `uv` for Python, a licensed SOLIDWORKS 2025
install, Ghidra 12.1.2 headless, and `cdbX64.exe` from the WinDbg MSIX package.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File re\binaries\Fetch.ps1 -VerifyOnly
uv run python re\tooling\ghidra\Sigtable.py
uv run python re\tooling\ghidra\Generation\SerializeMap.py
uv run python re\tooling\ghidra\Validation\VerifyLayout.py
```

The first verifies the external licensed installation. The other three re-derive `data/SignatureTable.json`,
`data/SerializeMap.json` and `data/VerifyLayout.json` from the binaries plus the traced
segmentations, and they rewrite those files in place — a clean `git diff` after running them is the
cheapest end-to-end check that the recorded tables really do come out of the recorded bytes.

`tooling/README.md` states, per script, what still needs inputs that live in the gitignored
`.rescratch/` working directory (the `.SLDPRT` corpora and the multi-megabyte Ghidra dumps).

## What is deliberately not here

- The Ghidra 12.1.2 distribution (3.4 GB) and its release zip (573 MB). `tooling/ghidra/Setup.md`
  has the download URL, the exact filename and its byte size.
- The portable FreeCAD used to author `.FCStd` inputs (2.2 GB).
- The `.SLDPRT` / `.SLDASM` corpora. The real-world corpus already lives in the repository at
  `solidworks/examples/`; the authored corpora live in `.rescratch/{corpus,corpus2,trace,donors,arc,grammar}/parts`
  and are referenced by path, not copied. `solidworks/corpus/README.md` maps every corpus to its
  location and to what it proves.
- Raw cdb logs (~3.4 MB) and the decompiled C dumps (~24 MB). The `cdb` scripts that generate the
  logs are in `tooling/windbg/`; the spec files and wrappers that generate the dumps are in
  `tooling/ghidra/`. The _conclusions_ are in `re/solidworks/` and the _segmentations_ in
  `re/data/segments/`.
- Ghidra project databases, `__pycache__`, and any generated `.SLDPRT`.

## Scope honesty

The SOLIDWORKS work reads SOLIDWORKS streams. Kit does not write SOLIDWORKS files. The removed
writer re-emitted typed recordings of saved streams with selected fields overridden, and typing
every byte did not change where the values and offsets came from: one saved part of the right
feature topology. Those families were recorded payloads, and donor content is banned from
production output. `tools/Donors/CheckReplays.py` fails CI if `src` contains any recorded field
operation or re-emission call. A generative serializer is the open work. `solidworks/README.md`
and `solidworks/CorpusCoverage.md` state exactly where the line falls.
