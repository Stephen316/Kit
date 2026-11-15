# lxml security override

## Expectation

Upgrading lxml should select the release that fixes the external entity advisory.

## Actual behavior

The locked cyclonedx-python-lib dependency caps lxml below version 6.
An ordinary package upgrade therefore keeps the vulnerable 5.4.0 release.
The [upstream advisory](https://github.com/lxml/lxml/security/advisories/GHSA-vfmq-68hx-4jfw)
requires version 6.1.0 or later.

## Workaround

Set `lxml>=6.1.0,<7` in the uv overrides and regenerate `uv.lock`.
Keep the SBOM scanner enabled to verify compatibility on the merge-group candidate.
An override resolves package metadata conflicts but does not establish runtime compatibility.
