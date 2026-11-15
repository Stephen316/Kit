# Provisional SOLIDWORKS scope archive

The SOLIDWORKS scope control attempt at `c996f65f1745aad9aa7a82f89537eeb2f14303ee` saved its automatic case before failing to author the complete three-case campaign. The retained archive has SHA-256 `82141d768d1190bbc0193c0e30fdc06049a93ffdda88866b514c8d504213adfe`. Its MO 19000 `Contents/Config-0-ResolvedFeatures` stream has SHA-256 `fb38482b123c2ffcf28e5dfdfb2691ce03822dd4049e71f3719ef102fa48949a`.

```text
python re/automation/SolidWorksScopeArchive.py <private-retained-automatic-archive.SLDPRT>
```

The read-only report verifies the private archive bytes and the committed launcher, collector and specification. It also verifies the Git-pinned P04 through-all archive against its discovery receipt and replays its existing typed Cut reader. The normalized report SHA-256 is `4da047efcf25cb09ce91132549ef7c4d082bb851cf97edf1271cd9f4833079ac`. The private archive and licensed software stay outside the repository. [Native scope control and archive leads](CutScopeReadback.md)

## Bounded walk

Unique framed names and checked feature headers locate `ScopeBossA`, `ScopeBossB` and `ScopeThroughAll`. The walk derives downstream offsets from the named Cut, the packaged feature base, two counted transfer arrays and the atom ID array. It then follows both scope body records and closes at their shared feature-scope word.

| Record | Byte position or range | Checked observation |
| --- | --- | --- |
| `ScopeThroughAll` | 23,366 | Native feature ID 47, profile reference slot 350 |
| Atom body type and scope array | 23,593 and 23,597 | Body type 3, array present, two items |
| First scope body | 23,603–23,901 | Body 101, feature 32, recent atom 103 |
| Second scope body | 23,901–24,210 | Body 102, feature 40, recent atom 104 |
| Saved feature-scope word | 24,210 | Signed value 1 |

Each body has a framed local component, a face record with flags 512, and five nonnull typed surface references. Face and body fields identify earlier Boss features 32 and 40. The report checks both against the named Boss records, requires distinct body and producer IDs, and checks that both recent atom IDs belong to the enclosing Cut array.

The walk uses observed compact slots and earlier class declarations for this exact archive. The full incoming class map and the link from profile slot 350 to the separately named sketch remain unverified. The result records candidate producer ownership and leaves the native Auto-select value empty.

## Control contrast

The P04 through-all stream closes with one scoped body and the same saved feature-scope word `1`. Its typed end specification reaches a null depth slot. The provisional automatic archive demonstrates two serialized scope body entries under the same scope word. Interpreting the persistence of Auto-select still requires independently saved automatic and explicit A+B controls observed after reopening.
