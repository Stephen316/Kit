# Observer indices continue the target design

## Expectation

A cross-document subject in an entity frame uses a fixed observer index.

## Actual behavior

An entity frame lists its subjects with an observer index each.
For a subject in another design, Fusion continues the indices that the referenced design already uses.
The first new index is one more than the largest index on that object in the referenced design.

| Referenced object | Next index in native Part A | Next index in Kit part |
| --- | --- | --- |
| `FusionComponent` | 2 | 2 |
| `ComponentInstances` | 3 | 2 |
| `Features` | 1 | 0 |

The records of one placement use the component index and the two indices after it.

| Record | Observer index of the referenced component |
| --- | --- |
| `FusionComponentInstanceBrowserEntry` | Next index |
| `ComponentInstance` | Next index plus 1 |
| Ground override of the occurrence | Next index plus 2 |

The browser entry also refers to the instances and the features with their own next indices.

## Workaround

`ReadTarget` computes the three next indices from the referenced model.
`EmitAssembly` writes them into the new frames.
A target that has more observers gets higher indices.

## Evidence

- [Assembly authoring tests](../../../../../tests/convert/formats/FusionCodec/Links/AssemblyAuthorTests.py), cases `TestSlots` and `TestReplay`
- [Probe insert script](../../../../../re/Fusion/LocalOracle/LinksConfigs/ProbeAsmTargets.py)
- [Assembly authoring change](../../../../Changes/Fusion/Assembly/FusionAssemblyAuthoring.md)
