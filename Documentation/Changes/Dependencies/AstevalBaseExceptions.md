# asteval BaseException advisory

Dependabot alert [5](https://github.com/TryUniCAD/Kit/security/dependabot/5) identifies
[GHSA-89v8-rhwq-hf77](https://github.com/lmfit/asteval/security/advisories/GHSA-89v8-rhwq-hf77)
in asteval 1.0.6.
Expressions can raise BaseException subclasses that escape the interpreter's exception handling.
An injected SystemExit can terminate the caller process.

## Behavior

The uv override requires `asteval>=1.0.9,<2` instead of Checkov's exact vulnerable pin.
The lock selects asteval 1.0.10 under the existing seven-day package age policy.
The matching OSV suppression is removed.
Use `uv sync --frozen --all-groups --all-extras` to install the locked development tools.
The production dependency set is unchanged.

This upgrade also fixes the native memory flaw in alert 4.
The separate alert 4 PR necessarily contains the same package upgrade.
After either PR merges, preserve the patched version when integrating the other PR.

## Verification

The upstream advisory identifies 1.0.9 as the first patched release.
uv 0.13.8 regenerated the lock and changed only the asteval package version.
No local tests ran.
Remote CI validates the PR and the merge queue runs Checkov and dependency scanners.
Checkov compatibility and merge-group acceptance remain unverified until those jobs pass.

See the [security reference](../../Reference/Operations/Security.md)
and the [exact dependency pin gotcha](../../Gotchas/Packaging/AstevalSecurityOverride.md).
