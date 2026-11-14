# Technical term register

## Purpose

This register defines terms used in Kit documentation.
The Kit maintainer role owns changes to the register.
The language is English.
The version is the containing Git revision.

Entries identify project terminology, not ASD dictionary approval.
Use technical nouns as nouns unless an applicable technical-verb rule permits another use.
Preserve exact API spelling inside code spans.

## Terms

| Term                 | Meaning in Kit                                                          | Usage restriction                                             |
| -------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------- |
| adapter              | Component that reads or writes one registered format                    | Registration does not prove complete format support           |
| API                  | Application programming interface                                       | Use the documented public import                              |
| assembly             | Structure of component definitions, instances, and constraints          | Do not use as a synonym for a part                            |
| attestation          | Data reported by the writer about its output                            | It is not independent vendor evidence                         |
| B-rep                | Boundary representation of geometry and topology                        | A B-rep alone does not preserve a feature history             |
| capability           | Category of information represented in a document                       | Inspect each transfer result                                  |
| carrier              | Representation that retains information outside native target semantics | It can be unusable in the target application                  |
| case-specific value  | Value captured from one document or fitted to one case                  | Do not use it in production output                            |
| CI                   | Continuous integration                                                  | Identify the revision and run for each result                 |
| configuration        | Named variant of a CAD document                                         | Do not confuse it with SDK installation settings              |
| control document     | Known document used to check an oracle session                          | Record its identity and expected measurements                 |
| definition           | Shared component description in an assembly                             | An instance refers to a definition                            |
| destination          | Output path or writable stream                                          | Do not call it a source                                       |
| digest               | Hash value calculated from data                                         | It does not authenticate an untrusted sender                  |
| donor block          | Recorded vendor bytes from an unrelated document                        | Do not use it in production output                            |
| donor file           | Vendor-saved file used as a base, template, or patch target for output  | Do not read it in production code                             |
| feature history      | Ordered modeling operations and their dependencies                      | Do not substitute a mesh for this history                     |
| format vocabulary    | Declared format facts such as class names, enum codes, and field order  | Trace each entry to a finding in `re/`                        |
| instance             | One occurrence of a component definition                                | It has its own position and state                             |
| interchange document | Neutral `CadDocument` object                                            | It is not a vendor application session                        |
| lossless             | Result that meets all repository acceptance requirements                | Do not infer it from a successful API return                  |
| manifest             | Structured description stored with document data                        | A manifest can preserve information that a vendor cannot edit |
| mate                 | Constraint between assembly entities                                    | A name match does not prove equivalent behavior               |
| merge group          | Candidate revision created by the merge queue                           | Its checks differ from PR checks                              |
| native               | Representation in the target format's own structures                    | A mode label does not establish acceptance                    |
| oracle               | Isolated vendor application used for measurement                        | Never part of a production conversion                         |
| opaque               | Data whose semantics are not fully decoded                              | Preserve the limitation in result reports                     |
| payload              | Bytes associated with a document record                                 | Identify the format, role, and source                         |
| per-case table       | Table with one captured or fitted entry for each layout, size, or value | Do not use it in production output                            |
| PR                   | Pull request                                                            | Keep review evidence tied to its head revision                |
| proven constant      | Value that is the same in unrelated documents, with its reason recorded | Record the documents and the reason                           |
| replay               | Re-emission of the source document's own data                           | It does not prove translation to another format               |
| SDK                  | Software development kit                                                | Kit exposes a Python API                                      |
| source               | Input document or input bytes                                           | Preserve the original during conversion                       |
| tessellation         | Mesh representation for display                                         | It does not establish editable solid geometry                 |
| topology             | Relationships among bodies, faces, edges, and vertices                  | Keep identifiers consistent with geometry                     |
| vendor loadability   | Ability of the vendor application to open the output                    | Report the application version and measured result            |
| worktree             | Isolated Git checkout linked to a repository                            | Use a separate branch for the task                            |

## Exact machine values

The following values are protocol data.
Do not translate, capitalize, or paraphrase them in commands or result comparisons.

| Group              | Values                                                                                    |
| ------------------ | ----------------------------------------------------------------------------------------- |
| Transfer modes     | `native`, `mixed`, `carrier`                                                              |
| Carrier reasons    | `target_unsupported`, `writer_unimplemented`, `source_opaque`                             |
| Format identifiers | `solidworks.sldprt`, `solidworks.sldasm`, `freecad.fcstd`, `catia.v5`, `interchange.json` |
| Output error code  | `output_not_application_usable`                                                           |

Source: [transfer contract](../../src/convert/adapters/base/TransferContract.py).
See [format selection](../Tasks/SelectFormat.md) and [error recovery](../Tasks/Troubleshoot.md).

## Add a term

1. Find the term in the owning source.
2. Identify its meaning in the user task.
3. Check for an existing term with that meaning.
4. Add the preferred term and its restriction.
5. Record the change in the PR.

If two source identifiers differ, preserve both identifiers.
Explain the relationship instead of changing the public API spelling.
