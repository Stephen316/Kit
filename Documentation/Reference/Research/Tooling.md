# Research tools

## Purpose and scope

The research tools support decompilation, runtime tracing, and controlled vendor measurements.
They belong to research or validation workflows.
They are not production conversion dependencies.

## Tool map

| Location                           | Purpose                                       | Required context                       |
| ---------------------------------- | --------------------------------------------- | -------------------------------------- |
| `re/tooling/ghidra/`               | Static analysis and decompilation             | Exact binary hash and analysis project |
| `re/tooling/windbg/`               | Runtime traces                                | Compatible debugger and vendor build   |
| `re/tooling/harness/`              | Vendor measurement and sample creation        | Isolated licensed environment          |
| `re/tooling/ProgramDecomposition/` | Recovered program organization and generation | Recorded grammar and generation inputs |
| `re/binaries/`                     | Research binary evidence                      | License and provenance records         |

Read each tool's source and setup guide before executing it.
Do not assume that historical command paths match a new machine.

## Ghidra workflow

The [setup guide](../../../re/tooling/ghidra/Setup.md) describes the research environment.
Analysis scripts can rename archive overloads and map serializer functions.
Typed names help distinguish integer, floating-point, and string operations.
A recovered function name alone does not prove its field semantics.

Record binary identity, function address, version branch, and output artifact.
Keep decompiler output tied to the source binary.
Do not copy a build-specific address into a different build without verification.

## Runtime tracing

The tracing tools observe serializer and reader behavior.
Recorded state can include stream position, map count, and buffer boundaries.
Use the trace to check a proposed grammar.
Do not treat missing trace events as proof that a field is unused.

Debugger structure offsets require calibration.
A trace from one process can be invalid after a crash or build change.
Record process and control health with the results.

## Oracle harness

The harness uses vendor APIs only in isolated validation.
It measures output geometry and feature behavior.
It requires the controls described in [oracle evidence](Oracles.md).

Dialog handling can keep an experiment moving.
It must not silently convert a failed load into a successful measurement.
Record application errors and missing measurements.

## Generated programs

Program-decomposition tools organize recovered serializer logic.
Generated tables must retain their source evidence and deterministic inputs.
A generated file is not automatically correct or complete.
Production promotion still requires the repository's validation and acceptance gates.

## Prepare a research task

1. Identify the unanswered format question.
2. Select the smallest controlled sample family.
3. Record the vendor and tool versions.
4. Define the expected observation.
5. Run the authorized remote experiment.
6. Record confirmed, partial, and refuted findings.

The task result must distinguish observations from interpretations.
Do not publish an unmeasured hypothesis as product support.

## Sources

- [Research index](../../../re/README.md)
- [Ghidra setup](../../../re/tooling/ghidra/Setup.md)
- [Runtime trace tool](../../../re/tooling/windbg/Multitrace.py)
- [Serialization harness](../../../re/tooling/harness/Serialize.py)
- [Program generation](../../../re/tooling/ProgramDecomposition/GeneratePrograms.py)
