# Capability presence is not semantic coverage

## Expectation

A parametric-history capability might appear to prove that every feature has a portable editable definition.

## Actual behavior

At main `52dbbe55`, [capability inference](../../../src/interchange/document/models/DocumentCaps.py) marks history present for any timeline feature whose kind is not imported.
That condition also admits native-only or partially interpreted feature records.
The [SOLIDWORKS feature builder](../../../src/convert/adapters/solidworks/core/Adapter.py) can retain native definitions and unresolved termination codes.
Optional provenance and a successful model-reference check do not establish complete semantic interpretation.

## Workaround

Track required source concepts and unresolved fields separately from category flags.
Check each feature definition, constraint, reference and writer mapping against independent source evidence.
Require the native route acceptance described in the [A01 audit](../../Reference/Research/NeutralContractAudit.md).
Do not reinterpret `strict=True` or JSON reconstruction as that acceptance gate.

This finding is based on source inspection, not a new execution result.
