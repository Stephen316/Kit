# Soupsieve advisories

Two advisories against `soupsieve` 2.9.2 appeared during the PR #96 queue
runs. The candidate at 00:47 UTC passed OSV-Scanner. The
[candidate at 01:08 UTC](https://github.com/TryUniCAD/Kit/actions/runs/43342545800)
failed on [GHSA-4j63-6c4x-wfg4](https://osv.dev/GHSA-4j63-6c4x-wfg4) (medium,
fixed in 2.10.0) and [GHSA-mmhr-3c5m-f64f](https://osv.dev/GHSA-mmhr-3c5m-f64f)
(high, fixed in 4.0.0). Every queue candidate then failed `CI Agg`.

## Behavior

- `[tool.uv].override-dependencies` requires `soupsieve>=4.0.0`. The lock
  resolves 4.0.1. `soupsieve` is a development dependency through
  `policy-sentry` and `beautifulsoup4`.
- `[tool.uv].environments` limits the lock to Python 3.11.5 and later.
  `soupsieve` 4 requires Python 3.11.5 or later. Without this limit, uv keeps
  2.10 for Python 3.11.0 to 3.11.4, and OSV-Scanner reports the high advisory.

The published `requires-python` stays `>=3.11`, and the runtime requirements
export is unchanged. `uv sync` for development on Python 3.11.0 to 3.11.4 now
fails. CI uses the latest Python 3.11 and 3.14. No advisory is ignored.

## Verification

The lock was generated with uv 0.13.8 to keep lock revision 5. With the
CI-pinned uv 0.12.5, `uv lock --check` and the dry runs of both CI
`uv sync --frozen` commands passed. No tests ran locally. The next queue run
gives the OSV-Scanner verification.
