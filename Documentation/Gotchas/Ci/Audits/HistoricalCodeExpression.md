# A history scan can mistake source syntax for a credential

## Expectation

The generic credential rule appears to identify a secret in historical SOLIDWORKS adapter code.

## Observed behavior

The finding points to line 1,037 of
[`Core.py` at `86ab1082`](https://github.com/TryUniCAD/Kit/blob/86ab1082a65054afb2c2022c77b18cd3a6b59908/src/convert/adapters/solidworks/resolved/Core.py#L1037).
The extracted value is the unquoted Python argument `axis_kind=None`.
The preceding offset variable supplied the detector's keyword context.
That value is source syntax rather than a credential literal.
The [original scanner log](https://github.com/TryUniCAD/Kit/actions/runs/43691519928/job/132743056959) records the rule, commit, path, and line.

## Resolution

Extend only the matching default rule with an `AND` exception for the complete historical commit,
anchored source path, and anchored extracted value.
Avoid a whole-file or whole-commit exemption.
Run the same expression through the actual scanner without that context and require detection,
then run the complete original history scan.

The pinned scanner's [configuration guide](https://github.com/gitleaks/gitleaks/blob/v8.30.1/README.md#configuration)
describes rule-specific conjunctions.
Its [implementation](https://github.com/gitleaks/gitleaks/blob/v8.30.1/detect/detect.go#L704-L825)
checks all supplied commit, path, and value conditions.
See the [repair entry](../../../Changes/Ci/PostMergeAuditRepairs.md).
Keep the historical path spelling when current source directories move.
See [historical scan path identities](HistoricalScanPathsUseCommitSpelling.md).
