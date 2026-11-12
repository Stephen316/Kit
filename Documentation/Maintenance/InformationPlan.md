<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Information plan

## Purpose

This plan controls the maintained Kit documentation.
It applies to the product revision stored with the document set.
The [standards register](../Standards/Scope.md) identifies the applicable editions and evidence limits.

## Readers and tasks

| Reader                   | Required knowledge                      | Main task                             | Entry point                                                    |
| ------------------------ | --------------------------------------- | ------------------------------------- | -------------------------------------------------------------- |
| Python integrator        | Python environments and file operations | Install Kit and call the API          | [Getting started](../GettingStarted.md)                        |
| Conversion operator      | CAD files and the intended output       | Select a format and evaluate a result | [Convert a document](../Tasks/ConvertDocument.md)              |
| Adapter developer        | Python contracts and the source format  | Trace the read and write boundaries   | [Architecture](../Reference/Architecture/Overview.md)          |
| CAD researcher           | Vendor tools and experimental controls  | Record format evidence                | [Research method](../Reference/Research/Methodology.md)        |
| Contributor              | Git and PR review                       | Submit a documented change            | [Contribution workflow](../Reference/Overview/Contributing.md) |
| Documentation maintainer | Product behavior and technical writing  | Review and publish information        | [Review procedure](Review.md)                                  |

No page assumes that the reader has access to a private conversation.
Each task states its files, tools, permissions, and expected result.
Examples use public API names and do not require internal implementation imports.

## Information structure

| Location                     | Content                                            | Maintenance rule                        |
| ---------------------------- | -------------------------------------------------- | --------------------------------------- |
| `README.md`                  | Product entry point and principal limits           | Link to task information                |
| `Documentation/Tasks/`       | Procedures for user outcomes                       | Include failure recovery                |
| `Documentation/Reference/`   | API, model, adapter, and research explanations     | Link to owning source                   |
| `Documentation/Standards/`   | Language rules, terminology, and conformance scope | Keep evidence gaps visible              |
| `Documentation/Maintenance/` | Planning, review, and delivery procedures          | Record process evidence                 |
| `Documentation/Changes/`     | Behavior changes and historical verification       | Preserve event meaning and source links |
| `Documentation/Gotchas/`     | Unexpected behavior and workarounds                | Link to the current guide               |

## Responsibilities

| Role                     | Responsibility                                      | Required record                          |
| ------------------------ | --------------------------------------------------- | ---------------------------------------- |
| Change author            | Update affected information with the product change | PR and change entry                      |
| Technical reviewer       | Compare statements with source behavior             | Findings tied to a revision              |
| Language reviewer        | Check terms, grammar, and procedure structure       | Scope and unresolved words               |
| Documentation maintainer | Resolve defects and control publication             | Release record                           |
| Repository administrator | Authorize queue enrollment or merge                 | Explicit request and verified permission |

One contributor can perform more than one role.
Record who performed each review.
Role definitions do not appoint a person or add a GitHub approval requirement.
The configured automated review and repository gates remain in force.

## Change control

1. Identify the changed user task.
2. Record the affected audience and product revision.
3. Update the task and reference pages together.
4. Add a separate [change entry](../Changes/Index.md) for each repository addition.
5. Update the term register when terminology changes.
6. Complete the review procedure on the proposed revision.
7. Publish only the authorized document set.

Documentation work belongs in the same PR as its product change.
For a documentation-only correction, record the incorrect statement and its replacement.
Do not retain an unsupported product claim to avoid a documentation change.

## Accessibility and localization

The maintained source language is English.
No translated edition is declared by this plan.
Use descriptive headings, ordered steps, text alternatives, and tables with clear headers.
Provide essential diagram information in prose.
Do not rely on color or images for a required instruction.

If a translation is added, retain exact identifiers and commands.
Record the source revision and language-specific reviewer.
Mark a translation as stale when its source procedure changes.
Do not publish a translation as current without a review of changed meaning.

## Maintenance triggers

Review the affected pages when an API, adapter, dependency, error, workflow, or support claim changes.
Review the standards register before each documentation release.
Record user-reported defects through the [feedback procedure](Feedback.md).
Keep unresolved defects linked to their affected pages.

## Success evidence

The review record identifies the revision, checked tasks, findings, and unresolved limitations.
CI proves only the checks it actually executes.
Publication evidence identifies the output location and source revision.
Neither record establishes full standards conformance without the complete requirement assessment.
