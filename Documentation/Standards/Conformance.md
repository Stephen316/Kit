# Conformance evidence and open requirements

## Status

Complete ASD-STE100 and ISO/IEC/IEEE 2651x conformance is unverified.
This document records the public-source mapping for the documentation expansion.
It does not reproduce normative clauses or certify the document set.

The source baseline is `b9a022e45` from the Kit repository.
The revision includes dependency updates and README presentation changes through `de20507ea`.
The integrated base also includes queue validation repairs through `7a878e689`.
The integrated base includes the reviewer configuration from PR #74 at `38ec9456d`.
The integrated base includes release packaging from PR #75 at `aebbc0b8a`.
It includes automatic release triggers from PR #77 at `c7fbd54d5`.
Its base revision is recorded in the PR.
The documentation revision is the Git commit containing this page.
The public-source review date is 2026-11-11.
See [the edition register](Scope.md) for publisher links.

## Evidence states

| State       | Meaning                                              |
| ----------- | ---------------------------------------------------- |
| Implemented | The document set contains the stated project control |
| Inspected   | Source inspection supports the stated behavior       |
| Unverified  | Required evidence is unavailable or not completed    |
| Not claimed | The revision makes no assertion of that outcome      |

An implemented procedure does not prove that someone performed it.
A documented role does not prove that a person accepted the role.
A CI result proves only the checks and revision shown by its run.

## Public-source mapping

The subject mapping below is an interpretation of the public publisher descriptions.
It is not a clause-by-clause compliance matrix.

| Standard                | Project application                                                               | Evidence                                                                                                  | Remaining requirement                                                                  |
| ----------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| ASD-STE100 Issue 9      | Short procedural and descriptive sentences, consistent terms, direct instructions | [Writing rules](WritingRules.md), [term register](Terminology.md), rewritten task and reference pages     | Complete dictionary and rule assessment remains unverified                             |
| ISO/IEC/IEEE 26511:2018 | Audience planning, ownership, maintenance, release records                        | [Information plan](../Maintenance/InformationPlan.md), [delivery](../Maintenance/Delivery.md)             | Full management requirements and actual process records remain unverified              |
| ISO/IEC/IEEE 26512:2026 | Scope, deliverables, supplier handoff, acceptance criteria                        | [Delivery requirements](../Maintenance/Delivery.md#define-a-supplied-document-set)                        | Formal acquisition applicability and complete agreement requirements remain unverified |
| ISO/IEC/IEEE 26513:2017 | Technical review, language review, task evaluation, defect disposition            | [Review procedure](../Maintenance/Review.md), [feedback](../Maintenance/Feedback.md)                      | Representative-user evaluation and complete normative assessment remain unverified     |
| ISO/IEC/IEEE 26514:2022 | User tasks, prerequisites, reference information, navigation, failure recovery    | [Index](../Index.md), [task guides](../Index.md#user-tasks), [API](../Reference/Overview/ApiReference.md) | Full design requirements and applicable normative references remain unverified         |
| ISO/IEC/IEEE 26515:2018 | Documentation changes with product changes and revision-bound review              | [Contribution workflow](../Reference/Overview/Contributing.md), [change index](../Changes/Index.md)       | Complete lifecycle process assessment remains unverified                               |

Do not claim that 26512:2018 is the current edition.
Do not use the unpublished 26513 replacement as the adopted normative edition.
Recheck both statuses before a later release.

## Coverage inventory

| Document group             | Coverage in this revision                                                                       |
| -------------------------- | ----------------------------------------------------------------------------------------------- |
| README and getting started | Product boundary, installation route, example prerequisites, acceptance limits                  |
| Seven task guides          | Installation, format selection, conversion, result evaluation, read/write, extraction, recovery |
| Twenty-two reference pages | Public API, architecture, models, adapters, data, operations, and research                      |
| Standards pages            | Scope, writing rules, terminology, and this evidence matrix                                     |
| Maintenance pages          | Information planning, review, delivery, and feedback                                            |
| Publishing                 | Import review, authorization boundary, wiki publication, revision readback                      |
| Change records             | Historical behavior and verification, with original event meaning retained                      |
| Gotchas                    | Expected behavior, observed behavior, and corrective action                                     |

Source code, binary fixtures, legal notices, and preserved historical standards are not rewritten as prose.
Research originals remain linked evidence.
The maintained research references explain their product boundary.

## Technical corrections

The revised information separates adapter registration from complete format support.
It removes the vendor oracle from the production conversion diagram.
It distinguishes reader strictness from output usability policy.
It identifies target-limit carrier handling in the registry.
It describes partial final stream writes and sequential B-rep extraction.
It identifies the missing stream count check when `write()` returns `None`.
It qualifies path rollback after a partial backup failure.
It requires an unchanged-candidate rebuild before oracle measurements.
It identifies the wiki default branch as the publication target.
It replaces unsupported hash-authenticity claims with integrity language.
It states binary archive sizes with `MiB` and `GiB`.
It qualifies cache and binary-offset observations by source family and vendor build.

## Validation record

The author compared public signatures, option construction, transfer policy, and destination staging with the source baseline.
The author also compared adapter metadata, model fields, archive limits, and serialization behavior with their owning sources.
Examples are documented instructions, not claimed execution results.
No local tests ran.
Prettier 3.6.2 formatting checks passed for the maintained Markdown and changed skill configuration.
Static inspection found no missing local Markdown targets or heading anchors.
Prose screening found no non-table sentences above 25 whitespace-separated tokens.
This screening does not implement the complete ASD word-count or dictionary rules.

Remote CI and the configured review must be read from the expansion PR's current head.
A PR link or review request is not a passing result.
Licensed vendor acceptance and merge-group acceptance are not claimed by this documentation change.
Wiki publication is not part of this revision.

## Close a conformance gap

1. Obtain lawful access to the complete applicable requirements.
2. Identify each normative requirement and its applicability.
3. Record an evidence link for each applicable requirement.
4. Complete the language dictionary and usage review.
5. Complete representative-user task evaluation.
6. Resolve findings on the candidate documentation revision.
7. Record the assessor, scope, date, and final decision.

Keep a requirement unverified until its evidence is available.
Do not convert a public abstract into an invented normative requirement.
