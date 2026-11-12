# Report and correct a documentation defect

## Purpose

Use this procedure when a page prevents a user from completing a task.
It applies to incorrect text, missing steps, unclear terms, and broken links.

## Before you start

Record the page path and the revision you read.
Record the Kit version, source revision, and relevant environment.
Remove secrets and private model data from the report.
For a security vulnerability, use the [private reporting procedure](../../.github/SECURITY.md).

## Report the defect

1. Open the [repository issue list](https://github.com/TryUniCAD/Kit/issues).
2. Check for an existing report about the same defect.
3. Identify the page and section.
4. State the task you attempted.
5. Quote the shortest text needed to identify the problem.
6. State the expected result.
7. State the observed result.
8. Include a public reproduction only when disclosure is permitted.

The issue is the feedback record.
A report does not establish that the product or documentation caused the failure.

## Triage the report

1. Compare the reported revision with the current source.
2. Identify the affected reader and task.
3. Determine whether the defect is in the product, documentation, or both.
4. Record the evidence and intended correction.
5. Link the correction PR to the report.

Prioritize instructions that can cause data loss or false acceptance claims.
Do not convert an unsupported feature into a documentation promise.

## Close the defect

1. Review the changed instructions against the implementation.
2. Update the related reference and task links.
3. Add a gotcha when the defect reveals unexpected behavior.
4. Record actual validation evidence.
5. Identify the revision that contains the correction.

Expected result: the report points to a reviewed correction and states any remaining limitation.
An issue closure alone does not prove that a published wiki contains the correction.

## Related information

- [Documentation review](Review.md)
- [Delivery and correction records](Delivery.md)
- [Error recovery](../Tasks/Troubleshoot.md)
