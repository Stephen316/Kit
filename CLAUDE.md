# Agent guidance

Follow [AGENTS.md](AGENTS.md). Agents MUST activate the repository's only skill,
[standard-pr-practice](.agents/skills/standard-pr-practice/SKILL.md), every time they
work on this repository, before any task, including investigation, documentation,
skill edits, implementation, and PR follow-up. Read every reviewer and its exact request comment
from the `Reviewers` array in the sole source of truth,
[ReviewBot.json](.agents/skills/standard-pr-practice/ReviewBot.json).

Follow the [documentation and gotcha rules](AGENTS.md#documentation-and-gotchas).

Agents MUST read and abide by the
[CAD success criteria](Documentation/Reference/Operations/CadSuccessCriteria.md) before any CAD
parsing, writing, conversion, verification, or reverse-engineering work, and before claiming that any
CAD output works. Every criterion is mandatory: no donor data, no CAD runtime, lossless, fully
parametric, vendor loadable, application usable, measured acceptance, honest attestation, complete
implementation, generalization, and traceable knowledge. Agents tasked with reverse engineering MUST
first read the [reverse-engineering instruction book](re/Playbook/README.md) in full and follow it.
See [CAD success criteria and reverse engineering](AGENTS.md#cad-success-criteria-and-reverse-engineering).
