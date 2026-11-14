# Native vertex edits can perturb TSM grip weights

A box and initial plane use weight 1 in every `0g` record. A native plane vertex edit produces one weight `1.0000000000000002`. Requiring exact unity rejects a valid native output; rounding it away loses a persisted value.

The fourth double of each grip record is its weight. Preserve finite positive weights exactly and reject nonfinite or nonpositive weights. Earlier binary inspection suggested that Fusion also rejects nonpositive weights; no black-box experiment confirms this. The typed writer emits enough decimal precision to round-trip the value without normalization.

[The edited source](../../../../../re/Fusion/LocalOracle/TSpline/PlaneEdited.tsm) binds this case.
