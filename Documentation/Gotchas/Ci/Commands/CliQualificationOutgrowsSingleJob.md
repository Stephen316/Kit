# CLI qualification coverage can exceed a single job budget

The earlier 766-case CLI run finished in 380.95 seconds on one runner. A later
775-case run progressed at roughly 72 cases per minute and reached 83 percent
before the unchanged ten-minute job timeout cancelled it. Passing archive or
static checks does not make that incomplete CLI execution successful.

Run core and qualification process groups in parallel while keeping every case,
each ten-minute limit, schema provenance, and locked setup. Keep both group
reports in the allowlist and require their joint success through the original CLI
report. Core must exclude exactly the directories explicitly collected by
Qualification so additions remain covered without duplicate execution.

See [the group workflow](../../../Changes/Commands/CliProcessGroups.md).
