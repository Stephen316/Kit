# asteval security override

## Expectation

A package upgrade should select the asteval release that fixes both sandbox escape advisories.

## Actual behavior

Checkov 3.4.3 requires asteval 1.0.6 exactly.
Checkov 3.4.5 still declares that exact requirement.
The [patched asteval release](https://github.com/lmfit/asteval/releases/tag/1.0.9) is 1.0.9.
An ordinary package upgrade cannot satisfy both requirements.

## Workaround

Set `asteval>=1.0.9,<2` in the uv overrides and regenerate `uv.lock`.
Keep Checkov enabled to verify compatibility on the merge-group candidate.
The same upgrade fixes both alerts, even when their reviews use separate PRs.
An override resolves package metadata conflicts but does not establish runtime compatibility.
