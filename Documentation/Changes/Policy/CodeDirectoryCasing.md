# Code directory casing

## Problem

The path checker validated file stems and directory density.
It did not validate directory names.
A complete tracked-tree scan could pass with lowercase internal directories.
PR and merge-group workflows also selected changed destinations, which could conceal unchanged violations.

## Change

`PTH003` checks every ancestor directory under `src/`, `tools/`, `typings/`, and `tests/`.
Internal directory names must contain PascalCase ASCII letters without digits.
The four conventional roots keep their existing spelling.
Existing public import packages and the external `defusedxml` stub package retain exact compatibility exceptions.
The [exception table](../../../tools/Policy/CompatDirs.py) contains those paths.
Exceptions do not apply to descendants or neighboring packages.

This migration renames 46 internal directories and moves 3,232 tracked files.
For example, `convert.Formats`, `interchange.Core`, `tests.Convert`, and `tools.Steering` now use their required casing.
Imports, source paths, workflow selections, package license paths, and maintained source links follow the new names.
The steering baseline receives path relocations only; its accepted findings are unchanged.
Historical secret-scan exceptions retain the path spelling from their recorded commits.
The existing `.gitleaksignore` fingerprint uses the reachable historical commit `86ab1082` and its lowercase `resolved` directory.
The rule-specific exception uses that same historical path.
Public API wrappers, public metadata, wire type names, and format identifiers retain their existing contracts.

The existing `Verify path policies` job now scans the complete tracked tree before its changed-destination scan.
It also runs process-level Git and command compatibility checks in remote CI.
The existing binary guard remains in place.
The rationale range check follows Git rename pairs back to their original source paths.
It preserves historical comments while continuing to reject newly added explanatory comments.

## Usage and limits

Stage intended path changes before running the index-based complete scan:

```sh
uv run python -m tools.Policy.CheckPaths
```

Use the canonical internal module paths in new code.
Retain supported public imports such as `convert.api` and `interchange.document`.
Research and external example paths retain their existing policy exclusions.
This change does not claim new CAD support or conversion acceptance.

## Verification

The original checker passed 11,211 tracked paths before directory-name coverage was added.
Source inspection identified the missing directory rule.
No local tests ran.
Static path, formatting, import, and steering validation and remote PR results are recorded with the delivery PR.
The new process checks exercise invalid ancestors, all four code roots, exact public exceptions, and revision scans.
Another process check verifies comment preservation across a rename and rejection of a subsequent explanatory comment.
Merge-group acceptance remains separate from PR validation.

The first merge-group history scan exposed an incorrectly renamed historical exception.
The [failed job](https://github.com/TryUniCAD/Kit/actions/runs/43821151397/job/133144280395) identified Python syntax, `axis_kind=None`, at the old path.
Source inspection confirmed that this expression contains no credential literal.
The follow-up restores the existing historical exception without broadening its commit, path, rule, or value constraints.
The scanner's negative control and complete history scan remain enabled for the next merge-group candidate.

See [the contributor policy](../../Reference/Operations/Policy.md) and [the directory coverage gotcha](../../Gotchas/Authoring/FileChecksMissDirectoryCasing.md).
See [historical scan path identities](../../Gotchas/Ci/Audits/HistoricalScanPathsUseCommitSpelling.md) before updating old scan fingerprints.
