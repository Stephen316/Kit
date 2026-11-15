# Feature contract checks can create an adapter import cycle

## Expectation

The shared native write guard can import Fusion's contract encoder when its module loads.

## Actual behavior

The [installed-wheel gate at `6fb599a9`](https://github.com/TryUniCAD/Kit/actions/runs/43672427965/job/132685201588) failed on Python 3.11 while importing `convert`.
Registry initialization loads `NativeWrite`, which loads `NativeFeatures`. Importing the Fusion encoder then initializes the Fusion adapter package, whose writer imports the still-initializing `NativeWrite` module.
An interpreter that already loaded these adapters can hide this ordering failure.

## Workaround

The intermediate repair imported the encoder only during contract evaluation. The final guard removes the encoder dependency and its unsupported native-tag exception after the [part-state qualification failure](NativePartStateAllowlist.md) showed that the proposed public contract was not reachable. Normal package initialization no longer crosses into the Fusion adapter from this guard.
Keep the installed-wheel fresh-interpreter import gate enabled; source type checks alone do not exercise import ordering.
The [native qualification change](../../../Changes/Research/Readers/NativeSemanticWriteQualification.md) records this repair and its pending current-head verification.
