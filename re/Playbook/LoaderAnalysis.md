# Phase B — Loader analysis

**Goal:** reverse engineer the vendor module that reads the file, so you know the data model it
expects, the order, type and width of every field, the legal domain of every key, what it does with
absent or illegal values, and which fields it recomputes. The loader is the specification; the file
is only one encoding of it.

**Inputs:** the stream inventory from phase A, the vendor install (or the tracked DLLs in
`re/binaries/`), REA, Ghidra headless, a debugger.
**Outputs:** a class → serializer map, a per-key table (type, range, default, validator, fixups,
version gate), named and annotated analysis databases, and recorded unknowns.

---

## 1. Find the modules that matter

A CAD install has hundreds of modules. You want the handful that open, read and validate the
document.

1. **Record identity first.** For every candidate module record path, version resource, size and
   SHA-256 (REA `inspect_signature`, `inspect_pe_resources`; or `sha256sum`). Every address you later
   cite is meaningless without the binary hash. `re/binaries/Manifest.json` is the format to follow.
2. **Search by vocabulary.** Grep every module for the stream names, member paths, XML tags, magic
   numbers and class names you saw in phase A:

   ```bash
   REA="npx -y rea-agents@6.7.0"
   for f in /abs/install/*.dll; do
     $REA execute-rizin-command "$f" "izz~Config-0-ResolvedFeatures" ;
   done
   ```

   Or use YARA rules over the whole install with the literal strings in ASCII and UTF-16LE.

3. **Search by API vocabulary.** Exports and RTTI names containing `Archive`, `Serialize`, `Stream`,
   `Read`, `Load`, `Restore`, `Persist`, `Document`, `Schema`, `Version`, `Factory`, `Registry`.
   `re/tooling/ghidra/Exports.py` dumps PE exports; REA `list_names`/`search_procedures` does the same
   inside a session.
4. **Follow the open path at runtime.** Record which modules load and which files are touched while
   the app opens a document (Process Monitor, `fs_usage`, REA `capture_process_scenario` for a CLI
   harness, Frida module enumeration). The modules loaded _during_ open, not at startup, are the
   short list.
5. **Check managed layers.** Many CAD APIs ship .NET interop assemblies and managed add-ins. Run
   `inspect_managed_artifact` and `inspect_managed_native_boundaries` on them to see which native
   DLL each API call lands in.

For SOLIDWORKS the answer was four DLLs: `sldmodu.dll` (model classes and serializers),
`sldarchiveu.dll` (the vendor's own archive implementation), `sldmfcu.dll` (container framing and the
signature table) and `swccu.dll`. Expect a similar split elsewhere: a container/IO module, an object
archive module, and one or more model modules.

---

## 2. Open them in REA

```text
open_binary { "path": "/abs/re/binaries/sldmodu.dll", "provider_id": "ghidra",
              "snapshot_path": "/abs/.rescratch/rea/sldmodu.snap" }
binary_overview {}
```

- Budget time: full Ghidra analysis of a 46 MB DLL took about 50 minutes with a 12 GB heap. Do it
  once, keep the snapshot, and share it with other agents.
- Ghidra rejects project paths with a component starting with `.`; use a directory junction or a
  non-dot path for the project (see `re/tooling/ghidra/Setup.md`).
- Confirm the provider and alignment with `binary_session {}` before long work.

---

## 3. Recover the data model

### 3.1 Class inventory from RTTI and vtables

C++ CAD kernels expose their class hierarchy through RTTI even when stripped of symbols.

1. Find RTTI type descriptors (`.?AV` names for MSVC, `_ZTS` for Itanium) with `search_strings`.
2. Walk complete object locators to vtables.
3. Identify the virtual slot that holds `Serialize` (or the vendor's equivalent). In SOLIDWORKS the
   reader dispatched **slot 5**, the vendor's own serializer, not MFC's slot 2. Find it by
   decompiling the archive's object-read routine and seeing which slot it calls on the new object.
4. Dump every vtable's serializer slot to get a complete map: class name → serializer address.
   `re/tooling/ghidra/Java/DumpVtableSlot.java` and `re/tooling/ghidra/Generation/SerializeMap.py`
   produced the 2607-class `re/data/Serialization/SerializeMap.json`.
5. Name every serializer in the REA session (`set_addresses_names` in bulk) so later decompilation
   reads in model terms.

### 3.2 Make field reads legible

Every field read in an archive-style serializer goes through a small set of primitives, usually
overloaded `operator>>`/`operator<<` or `Read<T>`/`Write<T>`. Untouched, a `double` read and a
`char` read look identical in pseudocode.

- **Rename the primitives by type** before decompiling serializers: `get_double`, `get_i32`,
  `get_u16`, `get_cstring`, `get_object`, `put_double`… Use the demangled parameter types.
  `re/tooling/ghidra/Java/RenameArchiveApi.java` does this for SOLIDWORKS; in REA use
  `set_addresses_names` on the import thunks and exports. This one step is the difference between
  usable and useless output.
- Identify the "read object" primitive separately. It reads a tag, looks up or creates the class,
  constructs the object and calls its serializer; its arithmetic is the object-renumbering rule.

### 3.3 Read the serializer of each class your corpus exercises

For each class that phase A or phase D shows in your streams:

```text
procedure_pseudo_code { "procedure": "swExtrudeFeature_Serialize" }
analyze_function      { "procedure": "swExtrudeFeature_Serialize" }
procedure_callees     { "procedure": "swExtrudeFeature_Serialize" }
```

From the pseudocode, write a field table:

| order | member offset | primitive    | type | condition / version gate | meaning (hypothesis) | evidence |
| ----- | ------------- | ------------ | ---- | ------------------------ | -------------------- | -------- |
| 1     | `this+0x0c`   | `get_i32`    | i32  | always                   | end condition enum   | ev_…     |
| 2     | `this+0x10`   | `get_double` | f64  | `version >= 0x1F4`       | depth (metres)       | ev_…     |

Then:

- **Follow the base classes.** Most of a record comes from the base-class serializers called first.
  The SOLIDWORKS work stalled on "we cannot serialise a feature record from nothing" precisely because
  the base classes were never fully decompiled. Do them.
- **Read the store branch too.** Serializers usually have one function with `if (IsStoring)`. The
  store branch frequently writes a string key next to the value for a debug/database path, which gives
  authoritative field names (`Value`, `EntIndex`, …).
- **Mine exported accessors.** `getDepth()`, `getType(int)`, `isReversed()` decompile to a single
  load from `this+offset` and bind names to member offsets wholesale.
- **Record version gates.** Every conditional on the document version is a layout difference between
  file eras. List the version constants and what each adds.
- **Record enum branches.** A `switch` on an enum in the serializer tells you every legal value and
  which values pull in nested records. Of twelve SOLIDWORKS end conditions, exactly two add a nested
  object; no corpus that never used them would have shown that.

### 3.4 Use the API's own vocabulary

- Dump the COM type library or .NET interop assembly for the public API (pywin32 `makepy`, comtypes,
  ILSpy, REA `inspect_managed_members` on e.g. `SolidWorks.Interop.swconst.dll`). You get every
  feature-definition interface, every property, and every enum with integer values.
- Map API properties to serializer members. The API getter and the serializer read the same member;
  `trace_native_values` from the API implementation usually lands on the same `this+offset`.
- API enum values often equal stored values. Treat that as a hypothesis to confirm on the corpus.
- The Python definitions of Fusion's `adsk` package shipped inside the install, and CATIA's type
  libraries, are the equivalent for those vendors. Locate them in the install rather than assuming a
  path; record the path and hash you used.

---

## 4. Find the boundaries of every key

"Boundaries" means the legal domain of each field and what the loader does at and beyond the edges.
This is what stops a writer from emitting a value the app silently changes, rejects or crashes on.

For each field, find in the loader:

| property               | where to look                                                                                      |
| ---------------------- | -------------------------------------------------------------------------------------------------- |
| type and width         | the read primitive                                                                                 |
| units and scaling      | constants multiplied after read (`0.001`, `25.4`, `π/180`), or comparisons against known constants |
| valid range            | comparisons after read: `if (v < 0 \|\| v > 11)`, `fmin/fmax`, assertions, early returns           |
| enum domain            | `switch` tables, jump tables, lookup arrays indexed by the value (`read_bytes` the array)          |
| clamping and repair    | writes back to the member after read: `if (x > max) x = max`, or `if (bad) x = 0`                  |
| neighbour fixups       | one field forcing another: in SOLIDWORKS one enum value forces a neighbouring flag to 1            |
| default when absent    | accessors that return a constant when a pointer is null: the "missing" revolve angle was 2π        |
| nullability            | null checks on object references; "no object" tags in the archive                                  |
| string limits          | buffer sizes, length checks, encoding conversion calls (UTF-16, code page)                         |
| count limits           | allocation sizes, loop bounds, `reserve` calls                                                     |
| cross-field invariants | comparisons between two members (start < end, knot vector length = control points + order)         |
| reference resolution   | how an id or index is looked up, and what happens when the target is missing                       |
| error severity         | does the path log and continue, mark the feature as failed, show a dialog, or abort the load?      |
| recompute              | is the value overwritten by a later rebuild step? Then it is derived.                              |

Use `trace_native_values` from the read site to see every use of the value: comparisons, stores into
members, arguments to validators. Use `procedure_callers` on validator functions (they are often
shared: `ValidateLength`, `CheckAngle`) to find every field they guard at once.

Write the result per field:

```text
ExtrudeFeature.endCondition
  type        i32 (get_i32 at sldmodu+0x…, ev_…)
  domain      0..11; switch at sldmodu+0x… (ev_…)
  nested      values 3 and 7 read an extra reference object (ev_…)
  fixup       value 5 forces reverseOffset = 1 (sldmodu+0x…, ev_…)
  illegal     >11 clamped to 0 in loader (ev_…); not measured in oracle yet
  default     n/a (always written)
  authored    yes (API IExtrudeFeatureData2.GetEndCondition, ev_…)
  confidence  partial — decompiled, values 3 and 7 not yet in corpus
```

---

## 5. Confirm dynamically

Static reading gives you the rule; a trace proves the code you read is the code that runs.

**The lesson that only runtime gives you:** in SOLIDWORKS, hooking MFC's `CArchive::ReadObject`
returned zero hits across a full open; the vendor had reimplemented the archive in its own DLL. Every
plan built on hooking the framework would have failed silently. Always confirm the hook fires.

Approaches, in order of effort:

1. **Breakpoint the read primitives** and log, per hit: stream position, map counter, value read,
   return address. Differencing consecutive positions gives every object's byte span; the counter gives
   the renumbering table. `re/tooling/windbg/Multitrace.py` and friends do this with cdb. With REA,
   attach Frida (`start_frida_session` mode `attach`, `load_frida_script`) and hook the same
   primitives.
2. **Filter by buffer length** so you log only the stream you care about.
3. **Time Travel Debugging.** Record one open with TTD, then query every read of a memory range
   afterwards without re-running the app.
4. **Coverage diffing.** Record coverage (`drcov`, Lighthouse/Lightkeeper/Cartographer) for two
   files that differ in one parameter. The basic blocks that differ are the branch that parameter
   selects.
5. **Write-path tracing.** Hook the same primitives during save to watch the writer emit fields in
   order with their values; compare to what the API reported for the same model.

Debugger traps that cost real time (from the SOLIDWORKS trace):

| trap                                                    | fix                                                                  |
| ------------------------------------------------------- | -------------------------------------------------------------------- |
| symbol lookups across hundreds of modules stall the run | `SYMOPT_NO_UNQUALIFIED_LOADS` first                                  |
| script directives collapse onto one line                | one command per line in included scripts                             |
| mangled export names rejected by the parser             | use the undecorated name                                             |
| deferred module-load breakpoint never fires             | the module was already loaded; set it at the initial break           |
| the hooked framework function is never called           | the vendor reimplemented it; find the real one from the export table |
| results drift after a crash                             | fresh process per run; controls before and after                     |

---

## 6. Probe boundaries in a research process

Static domains are hypotheses until probed. In a research copy of a file, set one field to each
interesting value and let the oracle report what happened (opens, repairs, clamps, rebuild error,
crash). Choose values from the loader analysis: each side of every comparison, every enum value,
zero, negative zero, NaN, ±infinity, denormals, the largest finite value, empty strings, maximal
lengths, null references, dangling references.

When per-file oracle runs are too slow, build an in-process harness that calls the vendor's own record
reader on a buffer (a Frida `NativeFunction` call or a small loader stub), and fuzz the field with a
grammar-aware mutator. Coverage-guided fuzzing (AFL++, WinAFL, Jackalope) over that harness discovers
branches you did not know to look for.

Record each probe as a measured row. A field's domain is _confirmed_ only when the decompiled rule
and the measured behaviour agree.

---

## 7. Version diffing

When a new vendor release ships:

1. Hash and catalogue the new modules.
2. Open old and new in REA; `compare_functions` on each known serializer, or run BinDiff / ghidriff
   across the whole module.
3. New conditionals on the document version are new fields. Changed switch tables are new enum
   values. Moved members are layout changes.
4. Re-run the phase C ladders on the new version and the phase D correlation, and update every field
   table with the version gate.

---

## 8. Recording and hygiene

- Name and comment in the analysis database as you go; export the snapshot and an evidence bundle
  (`export_evidence_bundle`) when a finding depends on them.
- Open questions go into `record_unknown` with the evidence that would close them, and into the
  vendor's findings file in `re/`.
- Cite the binary hash with every address. An address from another build may be unrelated code.
- Do not commit decompiled vendor listings. Commit the conclusions: field tables, addresses, enum
  values, rules.

---

## 9. Exit criteria for phase B

- [ ] Loader modules identified with hashes and versions.
- [ ] Class → serializer map for every class the corpus exercises (and the base classes).
- [ ] Read primitives renamed by type; read-object arithmetic understood.
- [ ] Field table per class: order, type, member offset, version gates, enum domains.
- [ ] Boundaries per key: range, default, nullability, fixups, clamps, cross-field invariants, error
      severity, recompute status.
- [ ] At least one runtime trace confirming the code read is the code that runs.
- [ ] Boundary probes measured for every field you intend to write.
- [ ] Unknowns recorded with the evidence that would resolve them.
