# Evidence

Reverse engineering produces plausible hypotheses far faster than true ones. Nearly every serious
error in the SOLIDWORKS work was a confident inference nobody measured. This chapter is how findings
are recorded so that the next agent can trust them, check them, and build on them.

---

## 1. Confidence vocabulary

Every field, rule and claim carries exactly one label. The vocabulary matches `re/README.md` and
`Documentation/Reference/Research/Methodology.md`.

| label         | meaning                                                                                                                      |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **confirmed** | Decompiled (or otherwise read from the loader) **and** reproduced by a real traced span, corpus record or oracle measurement |
| **partial**   | Decompiled, but nothing available exercises it: constant across the corpus, or a branch never taken                          |
| **not found** | Not recovered yet                                                                                                            |
| **refuted**   | A hypothesis that evidence disproved; kept so nobody pays for it twice                                                       |

A _partial_ offset is an address for a hypothesis, not a fact. Several SOLIDWORKS _partial_ fields
were uninitialised memory.

A correlation alone, without loader evidence, is at most a candidate. Label it _not found_ with the
candidate noted, or _partial_ once the loader read is found.

---

## 2. What every finding records

| item                 | example                                                                        |
| -------------------- | ------------------------------------------------------------------------------ |
| subject              | `ExtrudeFeature.depth[0]`                                                      |
| location             | stream, object class, object-relative offset or path                           |
| encoding             | f64 LE, metres                                                                 |
| meaning              | blind depth of direction 1                                                     |
| domain               | (0, 1e3] m; zero rejected by API; loader clamps negative to 0                  |
| authored / derived   | authored                                                                       |
| version gate         | present for document version ≥ N                                               |
| evidence             | REA Evidence IDs, binary SHA-256 + address, trace file, corpus family + hashes |
| held-out result      | parse 412/412, emit 412/412 on held-out split                                  |
| oracle result        | rung 5 measured, controls healthy, volume error 3e-16 relative                 |
| label                | confirmed                                                                      |
| refuted alternatives | "depth stored in mm as f32" refuted by ladder 7                                |

Write findings into the vendor's tree in `re/` as you make them, not at the end. An agent can die
mid-task; findings on disk survive.

---

## 3. Using REA's evidence machinery

REA already records most of what the table above asks for.

- **Cite Evidence IDs.** Every REA call returns an `evidence_id` (`ev_…`) bound to the target hash,
  provider and analysis profile. Put it in the finding.
- **Unknowns register.** Use `record_unknown` for each open question with its domain (e.g.
  `"solidworks/Config-0-ResolvedFeatures"`), severity, required authority (`controlled-replay` for an
  oracle measurement, `shipped-artifact` for a loader read) and recommended probes. Update it with
  `update_unknown` as evidence arrives; `verify_unknown_resolution` checks that the resolving
  evidence qualifies. `list_unknowns` is the open-questions page.
- **Reconstruction obligations.** For a writer, every field is an obligation: something the
  reconstruction must reproduce. `build_reconstruction_obligation_ledger` takes an evidence bundle,
  reviewed obligations and a manifest that binds each obligation to an owner, a parser/type, original
  cases, fixtures and a verifier, and fails closed on gaps. `evaluate_reconstruction_coverage` and
  `verify_reconstruction` report coverage. Use them to make "which fields does the writer still not
  derive?" a query rather than a guess.
- **Persist.** `export_evidence_bundle` writes the session's evidence to a chosen path. Export the
  bundle that backs a finding, keep it next to the finding (or in `.rescratch/rea/` with its hash
  recorded if large), and `import_evidence_bundle` it in a later session.
- **Snapshots.** `close_binary` with `snapshot_path` keeps the analysis database, including names and
  comments, for the next agent.

---

## 4. Machine-readable tables

Prose explains; tables are what tools consume. For each vendor keep:

- the class → serializer map (`re/data/Serialization/SerializeMap.json` for SOLIDWORKS);
- per-class field layouts with labels (`re/data/Layouts/`);
- the stream inventory and census (`re/data/Inventories/`);
- corpus indexes with file and manifest hashes;
- measurement results with controls (`re/solidworks/measurements/`).

Generate tables from scripts and commit the scripts. Re-running the scripts and getting a clean
`git diff` is the cheapest end-to-end check that recorded tables really come from recorded bytes
(`re/README.md` describes this for SOLIDWORKS).

---

## 5. Negative results

Record what did not work, with the same care as what did:

- hypotheses refuted, and by which evidence;
- functions hooked that never fired;
- streams deleted that broke loading;
- fields that looked like data and were uninitialised memory;
- searches that came back empty, with their exact scope (an empty search over a provider's string
  inventory does not prove absence).

A confirmed negative ("the operation is not a flag; it is implied by derived face-identity records")
closes a question and stops further searching. It is worth more than an open question.

---

## 6. Reporting

When you report progress:

1. State in the first line whether the success criteria pass, with the measured numbers.
2. Separate intermediate results (decoded streams, byte identity, coverage) from acceptance.
3. Distinguish decompiled, traced and measured facts.
4. Name the next blocking stream or field and that you are working on it. Do not offer a menu or ask
   whether to continue.
5. Link the findings files and evidence bundles.

---

## 7. Privacy and provenance

- Scrub user names, home directories and machine names from traces, manifests and logs before
  committing. Previous research leaked home paths into tracked files.
- Never commit customer files, licence files, vendor installers or decompiled vendor source listings.
- Record the provenance of every sample: who authored it, with what, and when.
