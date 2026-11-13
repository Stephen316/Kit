# Historical measurements without source hashes

## Expectation

A saved `ground_truth.json` beside a native file can appear to prove that the exact checked-in bytes were measured.

## Observed behavior

The A02 inventory found historical Fusion relative filenames and SOLIDWORKS absolute scratch paths.
The indexed observations do not establish a capture-time binding between each measured artifact and its current SHA-256.
Some records contain null measurements, load failures or zero-body results.
An adjacent filename or a report-level completion label does not resolve that evidence gap.

See the pinned [evidence index](../../../re/automation/Corpus.json), the [Fusion axis capture](../../../re/Fusion/Study/revolveaxes-36bd04ac77e1/ground_truth.json) and [historical SOLIDWORKS measurements](../../../re/solidworks/measurements/grammar/MeasureAuthored.json).

## Workaround

Keep original measurements, units, failures and JSON pointers.
Mark relative-path associations as candidates and historical observations as unqualified.
Obtain a receipt with the exact native hash, recipe digest, application build, rebuild, parameter edits and healthy controls before qualification.
Do not replace missing measured values with analytic expectations.
