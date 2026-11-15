# Grouped offline archive calibration

Pass `--compare-grouped` to compare two fresh private stores with one physical supervisor slot each.
Both arms use the same immutable manifest, fixed reader, logical A03 limit of 20 and configured CPU and memory reserves.
The singleton arm runs first.
The grouped arm uses group protocol 1, a one MiB strict aggregate footprint limit and the manifest's initial worker estimate as its group memory floor.
The configured worker stop limit remains unchanged.

```sh
uv run --frozen --no-default-groups --extra dev --python 3.14 python re/automation/Calibration.py --manifest CalibrationManifest.json --output GroupedComparison --compare-grouped
```

Use an unused output directory and the existing manifest format.
The fixed worker verifies the ordered private member manifests and decodes each group's members serially.
Each member keeps its own input digest, result and controller settlement.
The regular calibration sweep still uses singleton workers.

Each paired trial binds accepted result and receipt digests to the actual launches and A03 group claims.
The physical-session report records ordered members, claim footprint, observed worker CPU time and peak memory once per session.
The throughput rate counts completed archives over the existing supervisor interval.
An arm needs clean cleanup, complete telemetry and the existing one-second actual overlap before comparison.
The grouped arm also needs a real multi-member archive session.
Both arms must produce the same neutral output digest under the same source, host and package identity.
The paired comparison reports measured gain and keeps concurrency recommendations in the regular sweep.

See [offline calibration](../../../Reference/Research/OfflineCalibration.md) for reserves and measurement limits.
