<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Deliver a documentation revision

## Purpose

Use this procedure to accept and publish a reviewed document set.
It also defines the project handoff for documentation supplied by another contributor.
The [standards scope](../Standards/Scope.md) identifies the limits of ISO conformance evidence.

## Before you start

- Identify the requested audience and tasks.
- Identify the product revision and documentation revision.
- Read the completed [review record](Review.md).
- Confirm the authorized publication destination.
- Record unresolved defects and standards gaps.

An implementation request authorizes its repository PR.
It does not authorize a wiki update, queue enrollment, or merge.
Follow the repository workflow for those actions.

## Define a supplied document set

Record the following requirements before a contributor supplies documentation:

| Item        | Kit requirement                                                                     |
| ----------- | ----------------------------------------------------------------------------------- |
| Deliverable | Markdown source, navigation, change entry, and source references                    |
| Audience    | Named reader role and required knowledge                                            |
| Scope       | Product revision, tasks, formats, and excluded material                             |
| Language    | English with the project writing rules                                              |
| Evidence    | Technical review, language review, and actual CI results                            |
| Ownership   | Maintainer role for future corrections                                              |
| Rights      | Repository license notices and retained third-party attribution                     |
| Acceptance  | No unresolved incorrect commands, unsupported claims, or broken required navigation |
| Delivery    | Scoped PR with an immutable head revision                                           |

These are project delivery requirements.
They do not assert that a procurement contract or supplier assessment exists.
If a formal acquisition applies, record its statement of work and acceptance authority separately.

## Accept the revision

1. Compare the supplied files with the agreed scope.
2. Check the product and documentation revisions.
3. Review unresolved defects.
4. Confirm every applicable PR check on the current head.
5. Confirm each configured reviewer's identity, current-head approval, and native report results.
6. Record the accepted scope and any withheld conformance claim.

If the product revision changes, repeat the affected technical review.
If the documentation head changes, refresh the review and CI evidence.
Do not accept stale evidence as a current result.

## Publish

1. Obtain the required publication authorization.
2. Select the reviewed source revision.
3. Follow the [publishing procedure](../Publishing.md).
4. Record the published location and source SHA.
5. Read back the published revision.
6. Check the index, one procedure, and their source links.

Expected result: the published set identifies its source and verified scope.
A merged PR does not prove that the wiki changed.

## Correct or withdraw a publication

1. Identify the incorrect page and published revision.
2. Record the effect on the user task.
3. Correct the source through a new PR.
4. Repeat the affected review.
5. Publish the authorized correction.
6. Record the replacement revision.

If an incorrect instruction can cause data loss, identify it prominently in the correction record.
Preserve publication history and unrelated pages.
Do not silently change historical verification results.

## Release record

Record the source SHA, output SHA, destination, publication date, publisher, review links, and known limitations.
Record the product version and commit, because a package version alone can identify multiple source revisions.
Keep superseded revisions available through Git history.
