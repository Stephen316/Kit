# Capability documents can describe different revisions

## Expectation

The roadmap, README and format-selection guide should describe the same production capabilities.
A named future task should be distinguishable from current implementation.

## Observed behavior

At main `e04e7b78699d3f567409937007b00b567620078a`, the roadmap still awarded native SOLIDWORKS write credit.
The production writer had been removed.
That roadmap also called Fusion read-only, while the README documented its qualified public writer.
The format-selection guide incorrectly said that Fusion was absent from production discovery.

PR #94's broad future plan also included configurations and additional formats.
An absent current implementation did not make those tasks unrelated to that programme.

## Workaround

Use the [roadmap](../../../Roadmap.md) with its source revision and the [conversion backlog](../../Maintenance/ConversionBacklog.md).
Check current public adapter contracts before making support claims.
Check owning registers and live PR diffs before claiming available work.
Update these pages when production support changes.
Preserve historical change entries as dated evidence rather than current capability tables.

## Evidence

- [Earlier roadmap](https://github.com/TryUniCAD/Kit/blob/e04e7b78699d3f567409937007b00b567620078a/Roadmap.md)
- [Earlier selection guide](https://github.com/TryUniCAD/Kit/blob/e04e7b78699d3f567409937007b00b567620078a/Documentation/Tasks/SelectFormat.md)
- [Production README](https://github.com/TryUniCAD/Kit/blob/e04e7b78699d3f567409937007b00b567620078a/README.md)
- [Fusion adapter contract](../../Changes/Fusion/Adapter/FusionPublicAdapter.md)
- [PR #94 programme scope](https://github.com/Stephen316/Kit/blob/25d9104cebfa2106e0f950cc01c49b9b61d0c879/Documentation/Reference/Research/AutomationPlan.md)
