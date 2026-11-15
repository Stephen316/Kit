# Research artifacts

## Behavior

Research contributions retain CAD files, documents, independently authored tools, and recorded format knowledge.
Vendor software stays outside repository checkouts under the [research artifact policy](../../Reference/Research/ResearchArtifacts.md).
Agent guidance applies this restriction to proprietary DLLs, installers, SDK code, symbols, license files, and decompiled vendor listings.
Renamed files and compressed copies follow the same rule.

## Usage

Use an external licensed installation for analysis.
The [input guide](../../../re/binaries/README.md) describes external manifest verification.
Use `--dll` for a different signature-table input path.
Set `KIT_SOLIDWORKS_DLL` for additional vendor-backed compatibility verification in an authorized environment.
The CAD corpus comparison does not require vendor software.

## Limits

Ignore patterns cover common software formats, including mixed-case extensions.
They do not replace content inspection or authorize forced additions.
CAD fixtures, document streams, and research findings retain their existing scope and licensing.

## Verification

Source inspection covers the artifact inventory, executable signatures, archive members, and affected consumers.
Local tests are prohibited.
PR CI and configured review provide remote evidence for the proposed revision.
Vendor-backed verification requires the external licensed module.
Merge-group acceptance remains deferred until authorized queue enrollment.
