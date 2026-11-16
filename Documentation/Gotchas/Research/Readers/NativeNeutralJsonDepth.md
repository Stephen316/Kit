# Native neutral evidence can exceed shallow JSON limits

## Expectation

A full codec document from a native reader can enter the research comparator without removing retained source metadata.

## Observed behavior

The [owning native diagnostic](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6926364607) reported a Fusion neutral document with 141,402 JSON nodes and depth 51.
The comparator's initial depth limit of 48 refused that document before graph matching.
That refusal supplied no matching or semantic result.

## Workaround

The raw JSON limit is now depth 64, retaining the 500,000-node and 32 MiB bounds.
The typed semantic walk retains its separate depth limit of 48.
Full source metadata remains present and unresolved; it is not removed to fit the comparator.
Documents beyond the bounds still refuse explicitly.

The new process coverage supplies independently authored nested metadata within and beyond the raw limit.
No local reader, comparator or test execution was performed.
Hosted process execution and independent semantic qualification remain required.
