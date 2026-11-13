# Review path exclusions

## Problem

Automated reviewers examined `Documentation/` and the `re/` research workspace.
Their findings in these paths added review work without product value.
The `re/` workspace is exempt from repository code standards.
The [documentation review procedure](../Maintenance/Review.md) already covers `Documentation/`.

## Change

Two repository files now exclude `Documentation/` and `re/` from automated review.

| File                                       | Mechanism                                                             |
| ------------------------------------------ | --------------------------------------------------------------------- |
| [REVIEW.md](../../REVIEW.md)               | Review instructions that tell the reviewer to skip both directories   |
| [config.json](../../.greptile/config.json) | `ignorePatterns` with `Documentation/**` and `re/**` as glob patterns |

The `ignorePatterns` value is one string with newline-separated patterns.
Each pattern contains a slash, so it matches only at the repository root.

The [path policy rules](../../tools/Policy/PolicyRules.py) exempt `.greptile/config.json` from the PascalCase stem rule.
The provider requires this exact path.

## Limits

`REVIEW.md` is instruction context, not an enforced filter.
A reviewer can still read files in these paths for context.
A reviewer that reads only its merge-base configuration applies the change after merge.
A pattern in a hosted dashboard can differ from the repository file.
Changes in `Documentation/` still need the documentation review procedure.
This change does not change reviewer identities, report requirements, or readiness gates.

## Recorded verification

The JSON file was parsed, and its `ignorePatterns` value split into the two expected patterns.
No local tests ran.
Remote PR CI verifies path policy for the changed files.
Reviewer behavior on later PRs remains to be observed.
