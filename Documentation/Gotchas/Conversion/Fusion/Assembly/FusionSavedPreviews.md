# Exports of saved designs have no previews

## Expectation

Every Fusion archive export contains `Previews/big.png` and `Previews/small.png`.

## Actual behavior

The API export of a design after a cloud save had no `Previews` folder.

| Controls | Previews folder | Member count |
| --- | --- | --- |
| `R0_empty` to `R4_joint`, `S0_inserted` (not saved) | Present, with `big.png` and `small.png` | 28 |
| `R5_saved` to `R9_archive`, `S1_saved` (saved) | Absent | 25 |
| `P_A1_saved`, `P_B1_saved` (saved parts) | Absent | 27 |

The cloud bundle members of example1 contain only `Previews/small.png`.

## Workaround

Do not require a `Previews` folder when you read a container.
`ContainerDirs` writes the `Previews/` folder entry only when previews exist.

## Evidence

- [Native controls](../../../../../re/Fusion/LocalOracle/LinksConfigs/LinkEvidence.json), field `member_count`
- [Container folder planner](../../../../../src/convert/formats/Fusion/ContainerCodec/ContainerDirs.py)
