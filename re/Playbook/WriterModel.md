# Phase E — Writer model

**Goal:** turn the field map into a model that can emit a complete native file from a neutral,
vendor-independent description, with every byte derived from format knowledge, and prove with the
oracle that the target application opens it, shows correct bodies, and keeps a live, editable
feature tree.

**Inputs:** the grammar and field map from phase D, the boundaries from phase B, the
deletion/substitution map from phase A, the corpus and oracle from phase C.
**Outputs:** a research writer in `re/`, then a production writer in `src/` that satisfies every
item in the [CAD success criteria](../../Documentation/Reference/Operations/CadSuccessCriteria.md).

---

## 1. Model the document symbolically

Do not write a byte patcher. Write a model.

- **Nodes, not numbers.** Every object is a node; every reference is a pointer to a node. Indexes,
  ids, offsets, counts and lengths are computed at emit time, never stored in the model.
- **Typed fields.** Each node has typed fields from the grammar, with units in the model's own
  convention and conversion at the boundary.
- **Authored vs derived vs bookkeeping** are separate parts of the node. Authored fields come from
  the neutral model. Derived fields come from a derivation or are omitted. Bookkeeping comes from
  the emitter.
- **Version as a parameter.** The emitter takes a target format version and applies version gates
  from phase B.

The mapping from Kit's neutral model (`Documentation/Reference/Model/`) to the native node graph is
the writer. The mapping back is the reader. Build both from the same grammar.

---

## 2. The byte-identity gate

Before synthesising anything, prove the model on real vendor files:

1. Parse a vendor-saved file into the symbolic model.
2. Emit it again with every index, count, length, offset and checksum recomputed from scratch.
3. Compare byte for byte with the input (after decompression, if compression parameters are not yet
   reproduced; then also compressed).

If the output is byte-identical, the segmentation and the bookkeeping rules are right for that file.
The SOLIDWORKS work reached byte identity on 16 parts across 4 streams, and that immediately turned
into the ability to grow, shrink and reorder.

This gate is an instrument. It proves the model can represent the file. It does not prove a writer,
because the authored values came from the input. Never present it as acceptance.

---

## 3. Synthesis ladder

Climb one rung at a time. Each rung is measured by the oracle before the next starts.

| rung | what you emit                                                              | what it proves                                        |
| ---- | -------------------------------------------------------------------------- | ----------------------------------------------------- |
| 1    | Container only, with an empty but valid document                           | framing, directory, integrity fields, version stamps  |
| 2    | One sketch with one entity                                                 | sketch records, entity tags, placement                |
| 3    | One fully-defined sketch with dimensions and constraints                   | constraint and dimension records, references          |
| 4    | One feature from that sketch (extrude, depth from the model)               | feature records, end condition, references to profile |
| 5    | Same, across every value in its ladder, including values not in the corpus | generalisation of the rule                            |
| 6    | Several features, with dependencies                                        | ordering, renumbering, dependency references          |
| 7    | Every feature type in scope, then combinations                             | coverage                                              |
| 8    | Parameters and equations driving dimensions                                | parametric links                                      |
| 9    | Assemblies, then drawings                                                  | cross-document references                             |

At every rung, the emitted file must be produced from the neutral model alone. No rung may read a
vendor-saved byte at emit time, even inside `re/`, once you claim the rung as writer evidence. A rung
that only works with bytes copied from a sample has not been climbed.

---

## 4. Rules for each field class

| field class                        | rule                                                                                                   |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Authored                           | Emit from the neutral model through the confirmed encoding. Validate against the phase B domain first. |
| Derived, app regenerates it        | Omit, or emit the smallest valid empty encoding the loader accepts. Prove with the oracle.             |
| Derived, app trusts it             | Compute from the model with the derivation found in the loader. Confirm on held-out samples.           |
| Bookkeeping                        | Compute from the emitted graph: counts, lengths, indexes, offsets, checksums.                          |
| Noise (timestamps, GUIDs, session) | Generate fresh values with the correct type and format. Deterministic options for reproducible tests.  |
| Uninitialised in vendor files      | Emit the value the loader treats as neutral (usually zero), justified by loader evidence.              |
| Unknown                            | Not emitted. The writer refuses inputs that need it, with a diagnostic naming the field.               |

Respect every loader fixup from phase B. If the loader forces a neighbour field to 1 for a given enum
value, emit the 1; if it clamps out-of-range values, validate before emitting rather than relying on
the clamp.

---

## 5. Things that must be computed, never copied

- Object indexes and the class-definition table, from the emitted object order.
- Every length and count prefix.
- Container directories, sector chains, central directories and their offsets.
- Checksums and CRCs over the exact emitted bytes.
- Ids and GUIDs: freshly generated, unique, in the vendor's format.
- Version stamps for the target version you chose.
- Compression: any valid stream the loader accepts. Find out in phase B whether the loader cares
  about compression level or window size (usually not).
- Signature-like fields: computed from their rule. A per-file lookup table found in a DLL can be
  research evidence; production code may contain only a proven irreducible constant in its smallest
  form, as `NoDonorBlocks.md` describes for the single SOLIDWORKS signature row.

---

## 6. Oracle acceptance

Every rung, and every production claim, ends with the procedure in the success criteria:

1. Control measured before.
2. Fresh process; open the candidate; record load errors and every dialog the watchdog dismissed.
3. Rebuild; record rebuild errors.
4. Body count, volume, centre of mass (and area, bounding box) against the neutral model's expected
   values.
5. Feature tree node by node against the source feature list.
6. Change a driving dimension, rebuild, and confirm the geometry follows by the expected amount.
7. Control measured after; discard the batch if either control fails.

Also check, for confidence:

- **Save round trip.** Let the vendor app save the candidate, then parse the vendor's save with Kit's
  reader. The parsed model must equal the model you wrote. Differences show fields the app rewrote:
  fixups you missed, derived fields it recomputed, or values it rejected.
- **Edit survival.** After the dimension edit and a vendor save, Kit's reader must parse the new
  value from the vendor's file.
- **Held-out models.** Emit models whose parameter values and combinations never appeared in the
  corpus. A writer that only works on corpus values has memorised the corpus.

---

## 7. Promotion to `src/`

Research writers live in `re/`. Promotion means:

1. Every field the writer emits is _confirmed_ in the vendor's findings in `re/`.
2. The production code contains only declared vocabulary and rules, each traceable to a finding.
3. No file under `re/`, `tests/` or `examples/` is read at runtime; no captured table moved into
   `src/`.
4. No import, process launch or service call touches a CAD application.
5. Unsupported input fails with a diagnostic. No partial output, no carrier presented as native.
6. Integration and acceptance coverage at the conversion boundary, executed in remote CI and the merge
   queue (never locally, per `AGENTS.md`).
7. Oracle measurements recorded as acceptance evidence for the cases claimed.
8. `vendor_loadable` and `application_usable` set from those measurements.
9. A change entry and the relevant guide updated, as `AGENTS.md` requires.

---

## 8. Exit criteria for phase E

- [ ] Symbolic model with computed bookkeeping.
- [ ] Byte-identity gate passing on a varied set of vendor files.
- [ ] Synthesis ladder climbed for the scope claimed, each rung measured with healthy controls.
- [ ] Held-out models emitted and measured.
- [ ] Save round trip and edit survival checked.
- [ ] Every item of the CAD success criteria satisfied for the claimed scope, with numbers.
