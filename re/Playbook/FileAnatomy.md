# Phase A — File anatomy

**Goal:** know the file's structure end to end before decoding any record. By the end of this phase
you can list every stream or member, say how each is framed, compressed and versioned, and classify
each as authored parametric data, derived non-parametric data, or bookkeeping.

**Inputs:** whatever samples exist, plus the first small authored set (control pair, a few ladders).
**Outputs:** a container spec (ImHex pattern or Kaitai `.ksy`), a stream inventory with
classification, a noise-floor report, and a deletion/substitution map.

---

## 1. Catalogue the samples

1. Hash every file (`sha256sum`) and record size, origin (vendor-authored, user corpus, generated
   by Kit), vendor version that saved it, and locale of the install.
2. **Tag generated files and refuse them as test inputs.** The SOLIDWORKS work lost time because
   converter output that embedded a copy of the source was mistaken for a real conversion.
3. Keep real-world corpora (e.g. `re/solidworks/examples/`) separate from authored corpora. Real
   files teach coverage; authored files teach locations.
4. Note the save version of each file. Version gates change record layouts; a corpus from one era
   hides them.

---

## 2. Identify the container

Formats layer: an envelope, then streams, then records. Crack the envelope completely first. It is
the easiest layer and it gates everything else.

### 2.1 First look

```bash
xxd -l 256 sample.ext
file sample.ext
binwalk sample.ext
binwalk -E sample.ext
7z l -slt sample.ext
strings -n 6 sample.ext | head -200
strings -el -n 6 sample.ext | head -200
```

In ImHex, open the file, look at the entropy graph and the data inspector, and bookmark every region
whose entropy changes.

### 2.2 Recognise a known envelope, even when damaged

Check these before assuming a custom container. The SOLIDWORKS container turned out to be a standard
ZIP shifted by 8 bytes with three magic numbers replaced and stream names nibble-swapped. Recognising
"ZIP with cosmetic damage" saved weeks.

| envelope                | tell-tale bytes or structure                                                                 | examples in the wild                                                      |
| ----------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| ZIP                     | `50 4B 03 04` local headers, `50 4B 01 02` central directory, `50 4B 05 06` end record       | Fusion `.f3d`/`.f3z`, FreeCAD `.FCStd`, 3MF, OOXML-style                  |
| ZIP, shifted or patched | central-directory-like records with wrong magics; offsets that are consistently off by _k_   | SOLIDWORKS 2015+ `.SLDPRT`/`.SLDASM` (see `re/solidworks/container/`)     |
| OLE2 / CFBF             | `D0 CF 11 E0 A1 B1 1A E1`, 512- or 4096-byte sectors, FAT/MiniFAT                            | Inventor `.ipt`/`.iam`, Solid Edge `.par`/`.asm`, older formats           |
| CATIA V5 container      | `V5_CFV2\0` magic, its own directory and extent tables (not CFBF); `CATIA_V5 CB0001` folders | `.CATPart`, `.CATProduct` (see `src/convert/adapters/catia/Container.py`) |
| SQLite                  | `SQLite format 3\0`                                                                          | caches, some newer document stores                                        |
| Text-led                | a readable header line, then binary or text sections                                         | Pro/ENGINEER and Creo files often start with a `#UGC:` line; DXF; STEP    |
| Custom TOC              | a header with counts and offset/length pairs that tile the file                              | many                                                                      |

For a ZIP family container, REA does the inventory for you:

1. `open_binary` with the absolute path.
2. `inspect_artifact` for the member graph: paths, sizes, methods, CRCs, digests.
3. `extract_artifact` to materialise members for byte work.

If the ZIP is damaged, use `zipdetails --scan` and a Python script that searches for each record
signature, then compare the observed offsets with what the central directory claims.

### 2.3 Custom containers

When nothing standard fits:

1. **Look for a table that tiles the file.** Read the first and last kilobytes. Look for monotonic
   32/64-bit values that are less than the file size; check whether consecutive values differ by
   plausible region lengths.
2. **Look for counts.** A small integer followed by that many fixed-size entries is a directory.
3. **Look for names.** Stream names in ASCII or UTF-16LE near offsets are a directory.
4. **Find padding and alignment.** Runs of `00` or `FF` ending on 512/4096 boundaries indicate sector
   allocation.
5. **Write the hypothesis as an ImHex pattern** and watch it parse the whole file. A grammar that
   parses ten unrelated samples without error is a real grammar.

### 2.4 Integrity fields

Every container eventually has a field that must agree with the data: CRC32 in ZIP, sector chains in
CFBF, per-stream checksums, a whole-file hash, a "signature triplet" that must match the file id.

- First test the standard functions (CRC32, CRC32C, Adler-32, MD5, SHA-1, SHA-256, xxHash, FNV) over
  every plausible span.
- If none match, **stop doing arithmetic and look for a table in the binary.** The SOLIDWORKS
  signature triplet survived a 58-file cryptanalysis attempt; it was a 1000-entry lookup table in
  `sldmfcu.dll`. Search the loader DLLs for the known values with REA `search_bytes` and follow
  `xrefs`. See [Techniques.md §6](Techniques.md#6-crack-a-checksum-or-a-signature-that-is-not-arithmetic).
- If a check is a cryptographic signature meant to prove vendor origin, record that and stop (see
  the ethics boundary in [README.md §6](README.md#6-ethics-and-legal-boundary)).

---

## 3. Inventory every stream

Produce a table with one row per stream or member, for every sample family:

| column          | how to fill it                                                                                       |
| --------------- | ---------------------------------------------------------------------------------------------------- |
| name / path     | as stored, and decoded if obfuscated                                                                 |
| presence        | always, conditional (on what), or rare                                                               |
| size range      | across the corpus                                                                                    |
| compression     | none, deflate, zlib, zstd, LZMA, custom; test by trial decompression at offset 0 and scanned offsets |
| entropy         | after decompression; near 8 bits/byte means still compressed or encrypted                            |
| encoding family | XML, JSON, text, binary-tagged objects, fixed records, embedded known format (Parasolid, ACIS, PNG)  |
| version markers | any field that tracks the save version                                                               |
| references      | ids or names that point into other streams                                                           |
| classification  | authored, derived, bookkeeping, unknown (see §4)                                                     |

Script it. A census across the full corpus is cheap and finds conditional streams that a handful of
samples miss. `re/data/Inventories/CorpusCensusPerFile.json` is the SOLIDWORKS example.

### 3.1 Embedded known formats

Many CAD files embed a documented geometry or image format. Find and peel these first, because they
are free decoding:

| embedded format    | marker to search                                                                                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Parasolid transmit | the text header line starting `**ABCDEFGHIJKLMNOPQRSTUVWXYZ`, and `SCH_` schema-name strings in text and binary transmit data; confirm on your samples |
| ACIS SAT/SAB       | `ACIS BinaryFile`, `ASM BinaryFile`, or a SAT version line                                                                                             |
| PNG / JPEG / BMP   | `89 50 4E 47`, `FF D8 FF`, `42 4D` — thumbnails and previews                                                                                           |
| XML / JSON         | `<?xml`, `{"` after decompression                                                                                                                      |
| zlib / zstd        | `78 xx`, `28 B5 2F FD`                                                                                                                                 |

Treat each embedded format as derived until phase A §5 proves otherwise.

### 3.2 Object-serialised streams

Binary streams in Windows CAD apps are often MFC-`CArchive`-style object graphs: a class is defined
once by name (a tag, a schema number, a length-prefixed class name) and every later instance is a
small integer index into a running map. The consequences:

- Inserting or deleting one object renumbers every later reference.
- You cannot find object boundaries by diffing; you need the reader's arithmetic (phase B) or a
  runtime trace.
- A re-emitter that recomputes every index from a symbolic graph and reproduces the input byte for
  byte proves the segmentation (see [WriterModel.md §2](WriterModel.md#2-the-byte-identity-gate)).

Look for the tells: repeated `FF FF` followed by a schema word and an ASCII class name, then later
`80 xx`-style back-references. `re/solidworks/archive/Grammar.md` is the full worked example.

---

## 4. Classify parametric vs non-parametric data

For every stream, and later for every record, decide which of these it is.

### 4.1 Authored parametric data — the design intent

What a user typed or picked. It must be written exactly and completely.

- Feature records: type, operation (boss/cut/intersect/new body), end conditions, depths, angles,
  directions, draft, thin options, merge flags, selected profiles and references.
- Sketches: entities (lines, arcs, splines with control points and knots, ellipses, points, text),
  construction flags, the plane or face they lie on, and their placement frame.
- Constraints and dimensions: type, the entities they bind, driving vs driven, values, tolerances,
  expressions.
- Parameters, global variables, equations, units, design tables, configurations and their overrides.
- Names, descriptions, colours and materials when the user set them.
- Assembly structure: components, occurrences, transforms, mates/joints and their references,
  patterns, suppression state.
- Drawing intent: sheets, formats, views and their source model, view scale and orientation,
  dimensions and annotations, tables, layers.

### 4.2 Derived non-parametric data — recomputable

What the application computes from authored data.

- B-rep bodies (Parasolid, ACIS/ASM, CGM, OCCT) and their topology.
- Tessellation, display lists, edge polylines, silhouettes, previews and thumbnails.
- Mass-property caches, bounding boxes, face/edge identity maps and naming tables, rebuild state.
- Drawing view projections and hatches computed from the model.

### 4.3 Bookkeeping

Ids, counts, lengths, offsets, checksums, timestamps, GUIDs, save-version stamps, journal or
undo state, recent-file data, window state. Compute these from the model you write; never copy them.

### 4.4 How to tell which is which

| test                                                                                | authored       | derived                        |
| ----------------------------------------------------------------------------------- | -------------- | ------------------------------ |
| Changes when you edit a dimension?                                                  | yes, locally   | yes, often widely              |
| Changes when you rebuild without editing (save, rebuild, save)?                     | no             | sometimes                      |
| Changes on a plain re-save (control pair)?                                          | no             | sometimes (timestamps, caches) |
| Delete it: does the app still open the file and rebuild the same geometry?          | no (data lost) | often yes                      |
| Corrupt it: does the app repair it silently?                                        | rarely         | often                          |
| Present in the API's feature definition object?                                     | yes            | no                             |
| Read by the serializer and then overwritten by a recompute in the loader (phase B)? | no             | yes                            |

---

## 5. Deletion and substitution experiments

The map of load-critical vs cache is the cheapest high-value artefact in the project. Build it early.

For each stream _S_ in a known-good authored file, in a research copy only:

1. **Delete** _S_ (rewrite the container without it, fixing the directory and integrity fields).
2. **Empty** _S_ (zero length, or the smallest valid encoding of an empty payload).
3. **Substitute** _S_ from a different file of the same family (same feature topology, different
   dimensions).
4. **Stale** _S_: take _S_ from the same file before a dimension edit.

Measure each variant with the oracle: opens? feature count? bodies? volume and centre of mass? rebuild
errors? Record the result in a table like `re/solidworks/measurements/Measure.md`.

Interpretation:

- Opens and rebuilds identical geometry with _S_ deleted → _S_ is a cache. Do not author it until the
  writer works without it; then decide whether to emit it at all.
- Opens but geometry wrong when _S_ is stale → the app trusts _S_ without recompute in some path.
  This stream must be derived exactly, from loader evidence.
- Fails to open with _S_ deleted → load-critical. Find out from phase B whether the reader needs its
  _content_ or only its _presence_ (an empty but well-formed stream sometimes suffices).

These substitution experiments are research. They use vendor-saved bytes as probes. They never become
a writer strategy.

---

## 6. Measure the noise floor

1. **Control pair.** Author the same model twice through the API in two fresh sessions. Save both.
2. **Re-save pair.** Open a file, save it unchanged under a new name.
3. Diff both pairs stream by stream (after decompression). Every difference is noise: timestamps,
   session ids, GUIDs, hash-seeded orderings, allocator garbage.
4. Record each noise field with its location and apparent type (FILETIME, Unix time, GUID, counter).
5. Before trusting any later diff, mask the noise fields.

Watch for **uninitialised memory** serialised into the file: bytes that differ between control pairs
for no reason and have no meaning. Several SOLIDWORKS "partial" fields turned out to be exactly that.
Phase B tells you whether the writer ever initialises them; the writer you build must emit a value the
loader accepts (usually zero), derived from loader evidence, never copied from a sample.

---

## 7. Version and locale survey

- Save the same authored model in every version the vendor's "save as older version" supports, and
  open older files in the current version. Diff the record layouts. Version gates usually appear as
  conditional fields keyed on a document version read early in the stream.
- If you can, author the same model on a localised install. Real corpora are often localised
  (the SOLIDWORKS V8 engine corpus is Spanish), which breaks any name-based heuristic: feature names,
  sketch names, default plane names and material names are all translated.
- Record which strings are user data, which are localised defaults, and which are internal
  identifiers that never change.

---

## 8. Exit criteria for phase A

- [ ] Container grammar written (ImHex pattern or `.ksy`) and parsing every sample without error.
- [ ] Stream inventory for the full corpus, with compression, encoding and presence conditions.
- [ ] Every stream classified as authored, derived, bookkeeping or unknown, with the test that
      decided it.
- [ ] Deletion/substitution map measured with healthy controls.
- [ ] Noise-floor fields located and masked.
- [ ] Integrity fields identified, with a computation or an explicit open question.
- [ ] Findings and refuted hypotheses written into `re/<vendor>/container/` or equivalent.
