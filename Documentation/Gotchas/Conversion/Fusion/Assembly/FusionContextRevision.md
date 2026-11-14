# A version context names the cloud document

## Expectation

The `RevisionId` of a version context names one version of the referenced design.
It equals the `DocumentId` of the referenced design file.

## Actual behavior

The `RevisionId` names the cloud document of the referenced design.
It did not change when the referenced design got a new version.
It did not equal the `DocumentId` of any Fusion export.

| Observation | Result |
| --- | --- |
| Part A contexts in `R1_part_a` to `R9_archive` | One `RevisionId` value |
| Part A contexts after the update to version 2 in `R7_updated` | Same `RevisionId` value |
| `DocumentId` of the 15 native link exports | 15 different values, none equal to a context `RevisionId` |
| Kit part `KitAsmPartA`, uploaded and then inserted by Fusion | `RevisionId` equal to the `DocumentId` of the uploaded Kit file |

Each Fusion export writes a new `DocumentId`.
So a model read from an export does not hold the cloud value.

## Workaround

`EmitAssembly` writes the `DocumentId` of each target model as the `RevisionId`.
Pass the model of the exact file that was uploaded to the cloud.
Do not pass a model read from a Fusion export of a cloud design.

## Evidence

- [Native controls](../../../../../re/Fusion/LocalOracle/LinksConfigs/LinkEvidence.json)
- [Probe insert script](../../../../../re/Fusion/LocalOracle/LinksConfigs/ProbeAsmTargets.py)
- [Assembly authoring acceptance](../../../../../re/Fusion/LocalOracle/LinksConfigs/AsmAcceptance.json)
- [Assembly authoring change](../../../../Changes/Fusion/Assembly/FusionAssemblyAuthoring.md)
