# Diagnose a failed conversion

## Purpose

Identify the failure boundary before you change an input or option.
Use this procedure for public API calls and their output checks.

## Before you start

Keep the original source file.
Record the Kit source revision, Python version, operating system, and format identifiers.
Record the exception type and complete error message.
Do not include private CAD data or credentials in a public report.

## Procedure

1. Identify the failing operation: selection, reading, validation, writing, or acceptance.
2. Find the matching symptom in the table below.
3. Record structured error fields when available.
4. Apply the stated recovery action.
5. Repeat the operation only after its prerequisite changes.

Expected result: the report identifies the failure boundary and the evidence needed for repair.
Repeated execution of an unchanged unsupported input does not supply new acceptance evidence.

## Symptoms and recovery

| Symptom                           | Likely boundary        | Recovery                                           |
| --------------------------------- | ---------------------- | -------------------------------------------------- |
| `ModuleNotFoundError` for `kit`   | Import identity        | Import from `convert` in the installed environment |
| No matching adapter               | Format selection       | Compare the format with `available_adapters()`     |
| Ambiguous adapter                 | Writer selection       | Set `destination_format` explicitly                |
| `FileExistsError`                 | Destination protection | Select an unused path or authorize replacement     |
| Invalid archive, XML, or manifest | Input validation       | Obtain an intact supported source                  |
| `CapabilityLossError`             | Capability accounting  | Record the lost capabilities and target format     |
| `ApplicationUsabilityError`       | Output policy          | Inspect `issues` and carrier reasons               |
| Short destination write           | Final stream output    | Replace the failed stream before retrying          |
| Empty B-rep extraction            | Payload availability   | Check source content and read filters              |
| Vendor opens an empty model       | Product acceptance     | Record body count and reject the acceptance claim  |
| Vendor oracle control fails       | Validation environment | Discard the affected batch results                 |

The symptom table is diagnostic guidance.
The actual exception and source path determine the cause.

## Read a usability error

This example requires a real `bracket.SLDPRT` source and an unused destination.

```python
from convert import ApplicationUsabilityError
from convert import convert as ConvertDoc

try:
    Result = ConvertDoc("bracket.SLDPRT", "bracket.FCStd", allow_carrier=False)
except ApplicationUsabilityError as ErrorData:
    ErrorReport = ErrorData.to_dict()
    print(ErrorReport)
```

The handler records the failure.
It does not convert the failure into a successful result.

| Field                        | Meaning                                        |
| ---------------------------- | ---------------------------------------------- |
| `code`                       | `output_not_application_usable`                |
| `format_id`                  | Rejected writer format                         |
| `issues`                     | Specific policy failure reasons                |
| `carrier_reasons`            | Carrier reason for each affected capability    |
| `unimplemented_capabilities` | Capabilities with missing writer support       |
| `source_opaque_capabilities` | Capabilities with undecoded source information |
| `requirements`               | Reported external requirements                 |
| `dropped`                    | Reported capability loss                       |

## Recovery boundaries

Do not disable archive limits to make malformed input pass.
Do not substitute a vendor application in the production conversion path.
Do not classify carrier output as editable native output.
Preserve partial extraction or stream results as failed-attempt evidence until cleanup is authorized.

For an ordinary documentation defect, use [the feedback procedure](../Maintenance/Feedback.md).
For a vulnerability, use [the private security procedure](../../.github/SECURITY.md).

## Sources

- [Usability error](../../src/convert/adapters/base/UsabilityError.py)
- [Registry errors](../../src/convert/adapters/registry/RegistryErrors.py)
- [Output policy](../../src/convert/adapters/base/WritePolicy.py)
