# Expand CLI matrix names in aggregation process fixtures

The CI aggregation process simulator now expands `matrix.group` job names from
the workflow's own `matrix.include` group rows. This applies to both pull-request
and merge-group simulations, producing the actual Core and Qualification report
names instead of an unexpanded template.

The production allowlist correctly required both group reports. The simulator
previously supplied neither, so otherwise-complete scenarios kept waiting for
missing checks until their subprocess limits expired. Repeated failures exhausted
the policy job's ten-minute timeout. Before this fixture repair, head `08671487`
passed all 775 CLI cases and 2,959 archive cases with three existing skips.

Existing process-boundary cases now also verify failure and pending behavior for
both new reports, including queue run/check conclusions. Every original assertion
and production gate remains intact. No timeout is increased, and no local tests or
collection ran. Static validation and exact-head remote results are recorded in
PR #119.

See [matrix report fixtures](../../Gotchas/Ci/Commands/MatrixNamesNeedConcreteFixtureReports.md).
