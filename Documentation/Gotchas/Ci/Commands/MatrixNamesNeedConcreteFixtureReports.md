# Aggregation fixtures need expanded matrix report names

GitHub expands a job named with `matrix.group` into concrete reports. The fixture
workflow reader previously expanded only language and test-shard matrices,
leaving the CLI group template as a single literal name. The real aggregator then
correctly waited for the concrete required reports absent from the simulation.

Expand group names from the workflow's own matrix rows for both PR and queue
fixtures. Do not fabricate success from the allowlist or remove required reports.
Verify that failure and pending conclusions for each group still block completed
health evidence through the existing aggregator subprocess boundary.

See [the fixture correction](../../../Changes/Commands/CliMatrixReportFixtures.md).
