<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Review the documentation

## Purpose

Use this procedure before you publish changed Kit information.
It checks technical accuracy, task completeness, language, and presentation.
It does not replace repository CI or product acceptance.

## Before you start

- Identify the documentation revision and product revision.
- Read the changed pages and their source references.
- Read the [writing rules](../Standards/WritingRules.md).
- Identify the intended reader from the [information plan](InformationPlan.md).
- Obtain the PR check inventory and available review evidence.

Do not run tests locally.
Keep procedure execution and product tests in authorized remote CI.
A source inspection is not an executed procedure test.

## Technical review

1. Compare each public import with the package exports.
2. Compare each option with its callable signature.
3. Compare each default with the option construction code.
4. Compare each result field with its owning type.
5. Trace each recovery action to the relevant error path.
6. Check each support claim against its acceptance evidence.
7. Check each source link against the documented revision.

Expected result: every behavior statement has a source or an identified evidence gap.
If a claim exceeds the evidence, correct the claim before publication.

## Procedure review

1. Check that the purpose states a user outcome.
2. Check that prerequisites identify the required files and access.
3. Check that each step gives one ordered action.
4. Check that each example defines its inputs.
5. Check that each destructive action has a preceding caution.
6. Check that success has an observable result.
7. Check that failure has a recovery action or stop condition.

For remote task evaluation, use a reader who matches the intended audience.
Record their task, environment, starting state, observed outcome, and difficulties.
Record assistance that the page did not provide.
Do not infer usability from a reviewer's familiarity with the implementation.

## Language review

1. Check the preferred technical terms.
2. Check sentence limits for procedures and descriptions.
3. Check active voice and imperative instructions.
4. Check ambiguous pronouns and omitted articles.
5. Check exact command and identifier spelling.
6. Record words that lack a complete dictionary assessment.

A spelling checker cannot verify approved meanings or parts of speech.
A sentence counter cannot establish ASD-STE100 conformance.

## Presentation review

1. Open the rendered document set.
2. Follow the index links to each changed page.
3. Check heading order and link labels.
4. Check code fences and table column alignment.
5. Check diagrams with their text explanations.
6. Check the layout at a narrow viewport.
7. Check that essential information remains available without images.

Record unavailable render or accessibility evidence explicitly.
Do not describe a source-only inspection as a rendered review.

## Defect disposition

| Defect                            | Required action                                          |
| --------------------------------- | -------------------------------------------------------- |
| Incorrect command or API option   | Correct the command or option before release             |
| Unsupported lossless claim        | Remove the claim or provide matching acceptance evidence |
| Missing required step             | Add the step and repeat the affected review              |
| Broken navigation                 | Repair the target and incoming links                     |
| Unverified dictionary meaning     | Record the gap and withhold full STE conformance         |
| Missing complete ISO requirements | Withhold full ISO conformance                            |

## Review record

Record these fields in the PR or an attached review artifact:

| Field            | Required value                                                           |
| ---------------- | ------------------------------------------------------------------------ |
| Scope            | Changed pages and user tasks                                             |
| Revisions        | Product SHA and documentation SHA                                        |
| Reviewers        | Observed identity and review role                                        |
| Methods          | Source inspection, language review, rendering, or remote task evaluation |
| Results          | Findings, corrections, and remaining limitations                         |
| CI               | Run links, revision, and actual result                                   |
| Automated review | Verified responding account or app and reviewed SHA                      |
| Decision         | Approved scope or specific publication blocker                           |

Keep current-head approval separate from a request comment.
Keep PR CI separate from merge-group acceptance.
See [delivery](Delivery.md) for publication evidence.
