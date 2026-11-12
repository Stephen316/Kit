# Expand and control the documentation

## Problem

The reference pages contained broad support claims and limited task guidance.
Some pages confused carrier preservation, replay, and native target acceptance.
The document set lacked an explicit language policy and standards evidence record.

## Change

The revision adds seven user task guides, a standards register, technical terminology, and documentation maintenance procedures.
It rewrites the README, getting-started guide, publishing guide, and all 22 reference pages.
The index now separates user tasks, reference information, standards, and maintenance.

The guides explain installation, format selection, conversion, result evaluation, read/write operations, geometry extraction, and error recovery.
The maintenance pages cover audience planning, review, feedback, delivery, and publication evidence.
The standards matrix maps project controls to public ASD and ISO information.
It identifies evidence that remains unavailable.

## Behavior corrections

The README no longer promises complete format support or default reversible conversion.
The production diagram uses `CadDocument` and does not include a vendor oracle.
The API reference distinguishes `strict`, `allow_carrier`, `values`, and `write_values`.
The result guide explains the registry's treatment of target-limit carriers.
The conversion and B-rep guides make lossless and parametric acceptance unconditional.
They describe permissive runtime behavior without treating it as product acceptance.
The destination guides document partial stream writes and partial B-rep extraction.
The security and data references distinguish integrity hashes from authentication.
The README retains the wiki link, badge, star history, and banner removal from PR #71.

The contribution guide reads reviewer definitions from `Reviewers` in [ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json).
It requires each reviewer's current-head approval and passing native reports.
Reviewer configuration changes remain separate from this documentation revision.
This PR depends on PR #74 for that configuration and its implementation.

## Use

Start with the [documentation index](../Index.md).
Use [the writing rules](../Standards/WritingRules.md) for maintained prose.
Use [the review procedure](../Maintenance/Review.md) before publication.
Use [the conformance matrix](../Standards/Conformance.md) for the exact evidence boundary.

## Limitations

The user selected public standards sources.
Complete dictionary assessment and full normative ISO requirements are unavailable in this revision.
Full ASD-STE100 and ISO/IEC/IEEE 2651x conformance is therefore unverified.
The project controls do not constitute certification.

Historical research files and the preserved standards archive retain their original evidence.
No production conversion code changes.
No wiki publication, merge, or vendor acceptance is claimed.

## Verification

Verification includes source inspection and permitted static documentation checks.
Examples were not executed locally.
No local tests ran.
Prettier 3.6.2 formatting checks passed for the maintained Markdown and changed skill configuration.
Static inspection found no missing local Markdown targets or heading anchors.
Prose screening found no non-table sentences above 25 whitespace-separated tokens.
This screening does not implement the complete ASD word-count or dictionary rules.
Current-head remote CI and automated review provide the PR evidence.
Heavy acceptance remains deferred to an authorized merge-group candidate.

New behavioral observations are recorded in the [gotchas log](../Gotchas/README.md).
