# Techniques

Concrete recipes for problems that come up in every format. Each one names the tools, the steps and
what counts as a result. Addresses, paths and names in examples are placeholders.

---

## 1. Find a known float in a stream

1. Generate the candidate encodings for the value in every unit
   ([CorpusCorrelation.md §2.1](CorpusCorrelation.md#21-candidate-encodings-for-a-number)).
2. Search each normalised stream. For f64 values produced by unit conversion, wildcard the lowest
   mantissa byte and verify the decoded value within 1e-12 relative.
3. Repeat on the next sample of the ladder. Keep only offsets (object-relative) that hold the matching
   value in every sample.
4. Decode the bytes on either side: the neighbours are usually the other fields of the same record.

In ImHex, the data inspector shows every interpretation at the cursor; the pattern language can
then declare `double depth @ 0x…;` and you can watch it across files.

## 2. Find a float in the loader binary

Default values, unit factors and tolerances are constants in code or data.

- `search_bytes` (REA) or `/x` (rizin) for the f64 LE bytes: 2π is `18 2D 44 54 FB 21 19 40`,
  π is `18 2D 44 54 FB 21 09 40`, 0.001 is `FC A9 F1 D2 4D 62 50 3F`, 25.4 is `66 66 66 66 66 66 39 40`,
  1e-8 is `3A 8C 30 E2 8E 79 45 3E`.
- `xrefs` to each hit lists the functions that use it. A function that loads 2π right after a null
  check on a dimension pointer is the "default when absent" rule.

## 3. Find which code reads a stream

1. `search_strings` for the stream name in ASCII and, if missing, `search_bytes` for its UTF-16LE
   encoding (Ghidra can miss undefined literals).
2. `xrefs` from the string to the code; `resolve_containing_procedure`.
3. `procedure_callees` from there until you reach the stream-open call and then the first read.
4. Confirm at runtime: breakpoint or Frida hook on that function while opening a file that contains
   the stream, and on a file that lacks it.

## 4. Split an object-serialised stream into objects

1. Identify the read-object primitive in the archive module (phase B §3.2).
2. Trace it during a file open, logging the stream position at entry and exit and the class-map
   counter (cdb scripts in `re/tooling/windbg/`, or a Frida script that hooks the same function).
3. Consecutive entry positions give each object's span. The counter gives the index each new class
   definition receives.
4. Write a segmenter that reproduces those spans from bytes alone, using the tag grammar. Check it
   against the trace on every traced file.
5. Re-emit from a symbolic graph and require byte identity
   ([WriterModel.md §2](WriterModel.md#2-the-byte-identity-gate)).

## 5. Grow a repeated structure from _n_ to _n_+1

1. Take the count ladder samples _n_ and _n_+1 from the corpus.
2. Segment both into objects; align the object lists.
3. The inserted objects are the per-item block. Every other change is a counter, a length, an index
   shift or a reference.
4. Write the rule for each change in terms of _n_. Emit _n_+2 from the model and compare with the
   corpus sample _n_+2 (held out). Then measure _n_+2 in the oracle.

## 6. Crack a checksum or a signature that is not arithmetic

1. Try the standard functions over every plausible span: CRC32 (and variants with different init
   and xorout), CRC32C, CRC16 variants, Adler-32, Fletcher, MD5/SHA-1/SHA-256 truncated, xxHash,
   FNV-1a, MurmurHash. A brute-force harness over spans and functions is cheap.
2. Scan the loader modules with YARA rules for known constant tables (CRC tables, hash initial
   values). `capa` labels hashing routines quickly.
3. If nothing fits, **look for a lookup table**. Take known (input, value) pairs from your files and
   `search_bytes` for the values in the loader modules. Follow `xrefs` to the code that reads the
   table and the code that compares it with the file. `re/tooling/ghidra/Generation/ScanConsts.py`
   and `re/tooling/ghidra/Findtable.py` do this for PE files.
4. If the check is a cryptographic signature that proves vendor origin, stop and record it. Do not
   forge it.

## 7. Recover an enum's legal values and meanings

1. In the loader: find the `switch` on the field in the serializer or the code that consumes it.
   Jump tables give the full value set; `read_bytes` the table if needed.
2. In the API: dump the matching enum from the type library or interop assembly.
3. In the corpus: an enum sweep with every API value; record the stored value for each.
4. Reconcile the three. Values the loader accepts but the API never produces are legal-but-unreachable;
   do not emit them.

## 8. Tell authored from derived

1. Control pair and re-save pair: derived caches sometimes change; authored data does not.
2. Edit one dimension: authored change is local; derived change is wide.
3. Delete or stale the field in a research copy; measure in the oracle.
4. In the loader: is the value overwritten by a recompute after read? `trace_native_values` from the
   read site; look for later stores to the same member from rebuild code.

## 9. Map a field's legal domain

1. Collect candidate edges from the loader: every constant the field is compared against, every
   clamp, every switch case.
2. Generate research files with the field at each edge, one below and one above, plus special values
   (0, −0, NaN, ±inf, denormal, max finite, empty, null).
3. Measure each in the oracle: opens? repaired? value read back through the API? rebuild error?
   crash?
4. Write the domain as measured, and compare it with the decompiled rule. Agreement is _confirmed_.

For speed, call the vendor's own record reader in-process (Frida `NativeFunction`, or a minimal stub
that loads the module) on a buffer, and fuzz the field with a grammar-aware mutator.

## 10. Find where a UI action lands in native code

Useful when an exotic feature has no obvious API and you need its serializer.

- Windows: record the action with the macro recorder to get the API call; then find that API method's
  implementation through the interop assembly and `inspect_managed_native_boundaries`, or through the
  COM vtable.
- macOS: `trace_native_ui_action` maps a compiled UI action selector to its handler and callees;
  `observe_native_calls` records which functions run during the action.
- Electron/Chromium surfaces (Fusion): `list_electron_targets`, `inspect_electron_page`, and static
  analysis of the shipped bundle with `analyze_javascript_application` show which command identifier
  the UI sends to native code.

## 11. Diff two vendor versions

1. Hash both installs' loader modules.
2. `compare_functions` on each known serializer, or BinDiff/ghidriff on the whole module.
3. New version comparisons in a serializer are new fields; new switch cases are new enum values.
4. Re-run the version set from the corpus and confirm.

## 12. Read a text sibling to decode a binary

1. Save the same model as binary and as text (Parasolid `.x_b`/`.x_t`, ACIS SAB/SAT, DWG/DXF).
2. Parse the text form with the public documentation or an open-source parser.
3. Locate each text value in the binary form with known-value search. The text form gives meaning and
   order; the binary gives encoding.

## 13. Recover strings and their encodings

1. `strings -el` and FLOSS for UTF-16LE text in binaries and streams.
2. Check length prefix width and unit (bytes vs code units) on a name of known length with a non-ASCII
   character in it.
3. Check normalisation: NFC vs NFD (macOS file systems and some apps decompose). Kit has met NFD
   filenames in the SOLIDWORKS corpus already.

## 14. Get a type library dictionary for free

```bash
python -m win32com.client.makepy "SldWorks 2025 Type Library"
```

The generated module lists every interface, method, argument and enum value. For .NET interop
assemblies, `ilspycmd` or REA `inspect_managed_members` gives the same. Keep the generated file in
`.rescratch/`; commit only the enums and names you use, as vocabulary.

## 15. Confirm the hook you set is the code that runs

Every runtime plan starts with a hit counter. Open a file and check that the hooked function fired,
with plausible arguments, at least once. Zero hits means you hooked the wrong code: a reimplemented
framework, an inlined call, a different module, or a code path the file did not take.

## 16. Keep a probe from damaging the install

- Run probes on copies, in fresh processes, with controls before and after.
- Expect crash handlers to accumulate; kill them between batches.
- Keep a clean snapshot (VM or disk image) of the oracle machine and restore it when controls start
  failing.
