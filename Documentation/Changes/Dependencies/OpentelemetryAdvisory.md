# OpenTelemetry advisory

An advisory against `opentelemetry-api` 1.45.1 appeared after the PR #106 and #107 queue runs.
The [PR #92 queue candidate](https://github.com/TryUniCAD/Kit/actions/runs/43530545010) failed OSV-Scanner on [GHSA-mf5v-w3w3-f6cg](https://osv.dev/GHSA-mf5v-w3w3-f6cg).
It is medium severity and fixed in 1.45.2.
The candidate did not change `uv.lock`, so every queue candidate inherits the failure from `main`.

## Behavior

- `[tool.uv].override-dependencies` pins `opentelemetry-api`, `opentelemetry-sdk` and `opentelemetry-exporter-otlp-proto-http` at 1.45.2.
- It pins `opentelemetry-instrumentation-requests` and `opentelemetry-instrumentation-threading` at 0.66b2.
- `opentelemetry-sdk` 1.45.2 requires `opentelemetry-semantic-conventions` 0.66b2, and the 0.66b1 instrumentation packages require 0.66b1, so all five pins move together.
- The lock updates twelve `opentelemetry` packages. No 1.45.1 package remains.
- These packages are development dependencies through `semgrep`. The runtime requirements export is unchanged. No advisory is ignored.

All new versions were published on 2026-10-29, so they satisfy `exclude-newer = "7 days"`.

## Verification

The lock was generated with uv 0.13.8 to keep lock revision 5.
With the CI-pinned uv 0.12.5, `uv lock --check` passed.
The dry runs of `uv sync --frozen --all-groups --all-extras` passed for Python 3.11 and 3.14.
No tests ran locally. The next queue run gives the OSV-Scanner verification.
