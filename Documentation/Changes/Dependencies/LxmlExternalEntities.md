# lxml external entity advisory

Dependabot alert [3](https://github.com/TryUniCAD/Kit/security/dependabot/3) identifies
[GHSA-vfmq-68hx-4jfw](https://github.com/lxml/lxml/security/advisories/GHSA-vfmq-68hx-4jfw)
in lxml 5.4.0.
The default `iterparse()` and `ETCompatXMLParser()` configurations can read local files through XML external entities.

## Behavior

The uv override requires `lxml>=6.1.0,<7` and the lock selects 6.1.3.
This replaces the vulnerable dependency used by the development SBOM tooling.
The override supersedes the older cyclonedx dependency cap.
The matching OSV suppression is removed.

Use `uv sync --frozen --all-groups --all-extras` to install the locked tools.
The production dependency set is unchanged.
The other Dependabot alerts are handled separately.

## Verification

uv 0.13.8 regenerated the lock and changed only the lxml package version.
The selected release satisfies the seven-day package age policy.
No local tests ran.
Remote CI validates the PR and the merge queue runs the SBOM and security scanners.
Scanner compatibility and merge-group acceptance remain unverified until those jobs pass.

See the [security reference](../../Reference/Operations/Security.md)
and the [dependency cap gotcha](../../Gotchas/Packaging/LxmlSecurityOverride.md).
