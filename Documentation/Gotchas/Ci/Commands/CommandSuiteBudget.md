# Give CLI process coverage its own execution budget

An early workflow ran CLI processes and the native archive suite sequentially
under the archive job's 10-minute timeout. That assumed the CLI cases would
remain small. The earlier combined step already took 8 minutes 15 seconds;
expanded CLI coverage alone later took 269.30 seconds before archive execution.

Keep the required CLI and archive jobs separate. Preserve all cases, the locked
environment, schema verification, and each 10-minute limit. Register both job
names in the CI allowlist for pull requests and merge groups. The extra runner
adds setup work but avoids sharing one execution budget across both suites.
The expanded CLI cases also use [two required parallel groups](../../../Changes/Commands/CliProcessGroups.md)
to keep execution within those unchanged job limits.

See [the change and actual timing evidence](../../../Changes/Commands/CliProcessCi.md).
