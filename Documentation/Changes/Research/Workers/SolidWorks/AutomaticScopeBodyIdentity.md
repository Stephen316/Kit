# Bind both saved automatic-scope solids to resolved body IDs

Run the [pinned automatic-scope archive command](ProvisionalScopeArchive.md) with `--compare-repeat` and `--inspect-map`. In both retained saves, the active `Contents/Config-0-Partition` payload has schema `SCH_3701250_37102_13006` and expands to 18,721 bytes. The ordinary decoder returns one carrier with two derived closed regions. The opt-in replay also reads the saved native shell, region and body attribute records inside that payload.

| Body | Native owner | Native region at payload offset | Native shell at payload offset | Atom attribute and value offsets | Typed ResolvedFeatures identity |
| --- | --- | --- | --- | --- | --- |
| A | 7 | 279 at 17,819 | 46 at 9,888 | 17,957 and 18,259 | Atom 103, body 101, Boss feature 32 |
| B | 3 | 50 at 9,805 | 8 at 1,793 | 18,381 and 18,681 | Atom 104, body 102, Boss feature 40 |

Each native solid region (`0x13`) and shell (`0x0d`) point back to each other and name the same body owner. Each shell head leads through ten consecutive face references, with reciprocal previous and shell references at every face. Together the chains cover every decoded face, with one chain per closed region. Named `ATOM_ID_2001` attributes link the two kernel owners to the same distinct recent atom IDs carried by the [resolved scope rows](AutomaticScopeTypedCut.md). The independent [recipe geometry and mass measurements](AutomaticScopePartitionGeometry.md) agree with the resulting ownership.

The exact paired inspection report SHA-256 is `7d82892faf83ea65101ea3ac48ed370dac114555704749b80b7fd4ddd943972c`. The two non-inspection reports retain their previous hashes. This witness covers the pinned automatic saves and their partition schema. Ordinary conversion still returns its derived carrier. Persisted Auto-select and explicit body targeting require their own native controls.

The [P04 partition identity audit](P04PartitionIdentity.md) checks the same native links across all eleven one-body discovery captures.
