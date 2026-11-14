# A link to a Kit part has a zero physical GUID

## Expectation

The `PhysicalGuid` of an asset link row is a nonzero GUID.
Kit read this field with the strict manifest GUID reader, which rejects the zero GUID.

## Actual behavior

Fusion copies the `physicalChangeGuid` asset property of the referenced design into `PhysicalGuid`.
A Kit part has no `physicalChangeGuid` property.
Fusion then wrote the zero GUID in the link row.

| Referenced design | `physicalChangeGuid` property | `PhysicalGuid` in the link row |
| --- | --- | --- |
| Native Part A and Part B and the native subassembly | Present | Equal to the property in every fixture row |
| Kit part `KitAsmPartA` | Absent | `00000000-0000-0000-0000-000000000000` |

The zero value has the same wire form as other GUIDs, a UTF-16 text of 36 characters.

## Workaround

`ReadAssetHeader` accepts the zero GUID in the `PhysicalGuid` field only.
`EmitAssetHeader` writes it again.
The link GUID, the asset and the snapshot still reject the zero GUID.
`EmitAssembly` copies the target property, or writes the zero GUID when the target has none.

## Evidence

- [Probe insert script](../../../../../re/Fusion/LocalOracle/LinksConfigs/ProbeAsmTargets.py)
- [Assembly authoring tests](../../../../../tests/convert/formats/FusionCodec/Links/AssemblyAuthorTests.py), cases `TestZeroChange` and `TestKitNested`
- [Assembly authoring change](../../../../Changes/Fusion/Assembly/FusionAssemblyAuthoring.md)
