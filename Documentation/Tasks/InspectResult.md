<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Evaluate a conversion result

## Purpose

Determine what the writer reported and what still needs independent verification.
Use this procedure after `convert` or `write_document` returns.

## Before you start

- Keep the returned result object.
- Record the source file and source revision.
- Identify the information that the task must preserve.
- Identify the target application and version.

`convert` returns a `ConversionResult` with a nested `output` record.
`write_document` returns the `WriteResult` directly.
Do not assume these return types have the same fields at the same level.

## Procedure

1. Read the source and destination format identifiers.
2. Read the output path when the destination is a file.
3. Read `application_usable` and `vendor_loadable` separately.
4. Read `dropped` and `requirements`.
5. Inspect each item in `transfers`.
6. Record the writer metadata and compatibility mode.
7. Compare the result with the task requirements.

Expected result: each required capability has an identified representation and acceptance status.
An absent error does not supply missing vendor evidence.

## Result fields

| Field                | Meaning                                      | Interpretation                                    |
| -------------------- | -------------------------------------------- | ------------------------------------------------- |
| `document`           | Neutral document used for writing            | Available on `ConversionResult`                   |
| `output`             | Writer result                                | Available on `ConversionResult`                   |
| `transfers`          | Capability representation records            | Inspect each mode and carrier reason              |
| `dropped`            | Reported capability loss                     | Any loss fails lossless acceptance                |
| `requirements`       | External requirements reported by the writer | Unmet requirements prevent acceptance             |
| `application_usable` | Writer claim about application use           | Verify editing and rebuild behavior independently |
| `vendor_loadable`    | Writer claim about opening the file          | Verify in the target application                  |
| `roundtrip_safe`     | Writer-derived preservation predicate        | It does not prove cross-format editability        |
| `near_lossless`      | Writer-derived preservation predicate        | It does not relax repository acceptance           |

## Transfer modes and reasons

| Value                  | Meaning                                        | Action                              |
| ---------------------- | ---------------------------------------------- | ----------------------------------- |
| `native`               | Information uses native target structures      | Verify the required target behavior |
| `mixed`                | Information uses more than one representation  | Inspect the carrier reason          |
| `carrier`              | Information uses a preservation representation | Do not claim native editability     |
| `target_unsupported`   | The target lacks the capability                | Record the target limitation        |
| `writer_unimplemented` | The writer does not implement the translation  | Record the implementation gap       |
| `source_opaque`        | The source semantics remain opaque             | Record the decoding gap             |

`allow_carrier=False` does not reject every transfer with a carrier component.
The registry distinguishes target limitations from implementation and source-decoding gaps.
It also checks usability flags, external requirements, and dropped capabilities.
Read the complete [write policy](../../src/convert/adapters/base/WritePolicy.py) before designing a stricter application policy.

## Independent acceptance

The repository acceptance rule requires all relevant information to survive.
Vendor loadability alone is insufficient.
Carrier-only output and a non-editable replacement for source history fail the acceptance gate.
Task options cannot waive that gate.
The evidence must include these observations:

- Body count, volume, and center of mass.
- Units and tolerances for the comparison.
- The feature tree and its correspondence with the source.
- A change to a driving dimension.
- A successful rebuild with the expected geometry change.
- Assembly structure and constraints when applicable.
- Healthy control documents before and after the oracle batch.

Keep oracle execution in the isolated remote validation workflow.
See [oracle evidence](../Reference/Research/Oracles.md).

## If the task fails

If a required observation is missing, report acceptance as unverified.
If a required observation fails, report the measured failure.
Do not distribute incomplete output as a completed translation.
Do not substitute byte identity, a mode label, or a passing static check.

## Sources

- [Conversion result](../../src/convert/engine/EngineResult.py)
- [Writer result](../../src/convert/adapters/base/WriteResult.py)
- [Transfer contract](../../src/convert/adapters/base/TransferContract.py)
