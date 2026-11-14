# Mandatory CAD success criteria

## Change

The change adds the [CAD success criteria](../../Reference/Operations/CadSuccessCriteria.md) page.
The page collects every acceptance condition for CAD work in one list.
`AGENTS.md` and `CLAUDE.md` now require agents to read the page and to follow every criterion.
The repository skill lists the page as mandatory for CAD parsing, writing, conversion, and verification.

| ID       | Criterion                                                |
| -------- | -------------------------------------------------------- |
| C1       | No donor data                                            |
| C2       | No CAD runtime                                           |
| C3       | Lossless                                                 |
| C4       | Fully parametric                                         |
| C5 to C7 | Vendor loadable, application usable, measured acceptance |
| C8       | Honest attestation                                       |
| C9       | Complete implementation                                  |
| C10      | Generalization to held-out inputs                        |
| C11      | Traceable knowledge                                      |

## Usage

Read the page before CAD parsing, writing, conversion, verification, or reverse engineering.
Read it before any claim that CAD output works.
Use its checklist before a completion claim.

## Limits

The page does not replace the source standards.
The no donor blocks, no CAD runtime, lossless translation, and complete implementation standards stay authoritative.
The readable copies of those standards are byte-checked by CI, so the change does not edit them.
If the page and a source standard differ, the stricter requirement applies.

## Recorded verification

Each criterion was checked against its source standard and the acceptance paragraph in `AGENTS.md`.
Prettier 3 formatted the changed Markdown files.
No local tests ran.
Remote CI must supply its own results.
