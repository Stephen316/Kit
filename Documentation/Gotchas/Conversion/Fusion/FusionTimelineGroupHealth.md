# Timeline groups can report unknown health

## Expectation

Every valid timeline entry reports `HealthyFeatureHealthState`.

## Actual behavior

The uploaded bundle's `Group1` timeline entry returned `UnknownFeatureHealthState` (5) with an empty message. The document recomputed successfully, and none of its timeline entries reported warning or error health. The unknown state persisted alongside a working assembly with 87 timeline entries.

## Workaround

Distinguish concrete feature failures from non-feature or group entries. Record unknown states and their entry names; check the explicit warning and error enums when evaluating the whole timeline. Require healthy states where the expected entry is a specific modeled feature, as in the separately qualified two-feature extrusion.

The [native report](../../../../re/Fusion/LocalOracle/Bundles/NativeBundleAcceptance.json) records the group observation, enum mapping, successful rebuild, subsequent parameter edit, and save/reopen. This evidence does not imply that every unknown state is harmless.
