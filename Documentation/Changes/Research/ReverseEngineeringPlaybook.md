# Reverse engineering instruction book

## Change

The change adds an instruction book for CAD format research in `re/Playbook/`.
`AGENTS.md`, `CLAUDE.md`, and the repository skill now require it for reverse-engineering tasks.

| Chapter                                                         | Content                                                                 |
| --------------------------------------------------------------- | ----------------------------------------------------------------------- |
| [README](../../../re/Playbook/README.md)                        | Mandatory rules, the five-phase loop, and the quick start               |
| [Toolchain](../../../re/Playbook/Toolchain.md)                  | REA MCP tools and CLI commands by phase, open-source tools, vendor APIs |
| [File anatomy](../../../re/Playbook/FileAnatomy.md)             | Containers, streams, and parametric or derived data                     |
| [Loader analysis](../../../re/Playbook/LoaderAnalysis.md)       | Vendor module data models and the legal domain of each key              |
| [Generative corpus](../../../re/Playbook/GenerativeCorpus.md)   | Corpora from vendor APIs with a ground-truth manifest for each file     |
| [Shape catalogue](../../../re/Playbook/ShapeCatalog.md)         | Tiers of shapes, features, assemblies, drawings, and boundary cases     |
| [Corpus correlation](../../../re/Playbook/CorpusCorrelation.md) | Location of known values, grammar induction, and held-out prediction    |
| [Writer model](../../../re/Playbook/WriterModel.md)             | Symbolic models, synthesis steps, oracle acceptance, and promotion      |
| [Techniques](../../../re/Playbook/Techniques.md)                | Recipes for common format problems                                      |
| [Evidence](../../../re/Playbook/Evidence.md)                    | Confidence labels, REA evidence, unknowns, and reports                  |
| [Orchestration](../../../re/Playbook/Orchestration.md)          | Parallel agents, oracle ownership, and briefs                           |
| [Vendor notes](../../../re/Playbook/VendorNotes.md)             | State and starting points for each CAD vendor                           |
| [Checklists](../../../re/Playbook/Checklists.md)                | Phase exit criteria, anti-patterns, and a brief template                |

The change also updates these entry points:

- `re/README.md` sends readers to the book first and corrects a stale donor statement.
- `re/Methodology.md` identifies the book as the method of record and marks two wrong statements.
- The research method, research tools, and documentation index pages link to the book.

## Usage

Read `re/Playbook/README.md` in full before a reverse-engineering task.
Then read the chapter for the current phase.
Put the book and the [CAD success criteria](../../Reference/Operations/CadSuccessCriteria.md) in each sub-agent brief.

## Limits

The book describes research methods in `re/`.
It does not authorize vendor automation in production code.
It does not change any acceptance criterion.
Vendor container facts without Kit findings are marked as hypotheses to confirm on samples.
Example addresses and paths in the book are placeholders.

## Recorded verification

The REA tool names come from the tool list of the connected REA MCP server.
The CLI commands and options come from `npx -y rea-agents@6.7.0 --help` and the help of each cited command.
The float byte encodings in the techniques chapter were computed with Python `struct`.
Prettier 3 formatted the changed Markdown files.
No local tests ran.
Remote CI must supply its own results.
