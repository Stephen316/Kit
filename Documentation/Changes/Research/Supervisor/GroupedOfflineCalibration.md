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
An ineligible comparison keeps the trial observations, records its refusal reason and returns exit status `2`.
The paired comparison reports measured gain and keeps concurrency recommendations in the regular sweep.

See [offline calibration](../../../Reference/Research/OfflineCalibration.md) for reserves and measurement limits.

## Measured Windows comparison

The standalone run on `50a4892bf1b9aefef83dbf9e9b49d7378518c248` used 64 distinct historical Fusion discovery archives.
All 64 input digests, sizes and current Git blobs matched the pinned manifest.
The cohort excludes paired captures, qualification archives, holdouts and known byte aliases.
The manifest lists 9,670,016 input bytes and reserves two logical CPUs and 4 GiB of memory.
The host reported 20 logical CPUs, Python 3.14.6 and pywin32 312.

| Arm | Physical sessions | Archives completed once | Wall seconds | Archives per minute | Longest one-slot overlap |
| --- | ---: | ---: | ---: | ---: | ---: |
| Singleton | 64 | 64 | 245.914 | 15.615 | 6.627 s |
| Grouped | 10 | 64 | 66.792 | 57.492 | 4.092 s |

The ten group sizes were 7, 10, 7, 6, 8, 8, 6, 5, 5 and 2.
The largest actual A03 claim footprint was 1,046,636 bytes.
Both arms verified the complete CPU and RSS measurements and clean supervisor, claim, session and Job Object shutdown.
The group rate was 268.18 percent higher in this singleton-first pair.
The rates include Python and controller work at the actual Windows claim and settlement boundaries.
The experiment measured one host and one arm order.
Linux and macOS throughput remain unmeasured.

The canonical manifest SHA-256 is `fb7c3b15b789fcc1166e3735a6859b5c7271c391c1190a3955ffb4cc53b93c07`.
The calibration source SHA-256 is `ae4020a268a64e7e960efc8429df6fb9389ccea7fe0208b4c35ae1ac9a75506d`.
Both arms produced neutral-output SHA-256 `4f52325c1cef850bd63ef2ca3da80a623bad16c8f204e108ec4444c1477f2773`.
The private report SHA-256 is `7facbb5d25a9b59559ed85774f489ec0762c32e43d6412050fb2627669f56b48`.
The singleton and grouped physical-session reports have SHA-256 values `321e3519656c4b1b7d6fd9b23bbe1435d424ec9a77a33559a4a4efa111c92b9b` and `97a95b8e5150183be3d632d065e3b2958e0892fae653c0f2d23cc2aa9cb46823`.

The new hosted process case exercises both arms on a generated Fusion archive through the normal calibration command.
It verifies actual group membership and equal accepted output.
Hosted process verification of that case remains pending.
