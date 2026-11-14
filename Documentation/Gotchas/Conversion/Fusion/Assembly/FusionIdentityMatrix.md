# An identity placement has no matrix values

## Expectation

Every occurrence placement stores 16 matrix values.

## Actual behavior

Fusion inserted the Kit part `KitAsmPartA` at the origin without a rotation.
All six matrix fields of the new records were empty matrix values.
`MatrixValue.Entries` is `None` for each of them.
Placements that are not the identity store 16 values.

## Workaround

`EmitAssembly` writes `MatrixValue(None)` for an identity placement.
It writes the 16 values for every other placement.
A reader must treat an empty matrix value as the identity.

## Evidence

- [Probe insert script](../../../../../re/Fusion/LocalOracle/LinksConfigs/ProbeAsmTargets.py)
- [Assembly authoring acceptance](../../../../../re/Fusion/LocalOracle/LinksConfigs/AsmAcceptance.json)
- [Assembly authoring change](../../../../Changes/Fusion/Assembly/FusionAssemblyAuthoring.md)
