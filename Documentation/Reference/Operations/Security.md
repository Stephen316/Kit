<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Security boundaries

## Purpose

This reference identifies input, filesystem, and validation boundaries.
It does not claim that static checks prove freedom from vulnerabilities.
Use the [security policy](../../../.github/SECURITY.md) to report a vulnerability privately.

## Untrusted input

Treat CAD archives, XML, JSON, paths, and embedded payloads as untrusted data.
Format identification does not validate all contents.
The relevant reader must validate sizes, structure, and references.

Production conversion must not invoke a vendor application to handle an unsupported input.
Oracle tools belong to isolated validation environments.
The existence of an oracle path helper does not authorize a production runtime dependency.

## Archive limits

The FreeCAD archive reader checks member sizes, total expanded size, compression ratio, and entry count.
It also checks unsafe paths and unsupported archive entry types.
See [the exact limits](../Adapters/Freecad.md#resource-limits).

XML parsing has depth and node limits.
Embedded manifest parsing has a separate depth limit.
These controls address different forms of resource consumption.
Do not describe one limit as complete protection against every malicious input.

## Filesystem boundaries

The security path helpers validate their designated input and temporary paths.
Their guarantees apply only where callers use them correctly.
Output staging has its own destination behavior.
Do not infer a universal sandbox around every public API call.

The caller controls source and destination locations.
Use task-owned output directories and preserve original inputs.
A stream failure can leave partial bytes in a caller-owned stream.
B-rep extraction can leave earlier files after a later failure.

## Program boundary

Program-selection helpers support controlled tooling contexts.
They do not make arbitrary executable paths safe.
Keep vendor programs outside the production conversion path.
Record the actual binary and version for an oracle experiment.

## CI evidence

PR checks and merge-group checks cover different scopes.
Static analysis, dependency analysis, secret scanning, and integration checks each provide bounded evidence.
A successful scan describes its revision, configuration, and tool coverage.
It does not prove vendor usability or complete standards conformance.

Follow [merge queue operations](../../../MergeQueue.md) for the current check architecture.
Keep all applicable gates enabled.
Do not suppress a finding merely to make a status green.

## Report a problem

1. Preserve the affected revision and error evidence.
2. Remove secrets and private design content from public material.
3. Use the private reporting route for vulnerabilities.
4. Record ordinary documentation defects through the feedback procedure.

Expected result: the report reaches the appropriate channel with enough evidence for investigation.
This procedure does not authorize an agent to send a report without a user request.

## Sources

- [Path boundary](../../../src/convert/Security/PathBoundary.py)
- [Program boundary](../../../src/convert/Security/ProgramBoundary.py)
- [Archive validation](../../../src/convert/adapters/freecad/Archive.py)
- [Write boundaries](../Architecture/Engine.md)
- [Feedback](../../Maintenance/Feedback.md)
