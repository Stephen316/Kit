# Read saved SOLIDWORKS two-body through-all scope

The bounded Cut operation parser starts after the resolved Cut node with both earlier Boss owners, the reached configuration map and the selected contour edge IDs. It binds each saved body through typed surface references to the prior Boss's file, feature and clock. It retains the raw owner word alongside that join. [Typed Cut operation](../../../../../src/convert/adapters/solidworks/Resolved/Cut/ScopeOperation.py)

The licensed campaign supplied three exact MO 19000 controls. The independent native report verified their policies and body measurements before save, after reopening and after rebuilding. A read-only walk on those same saved archives reached the end of each resolved stream. [Native control archive hashes and measurements](../../Workers/SolidWorks/ThroughAllScopeNativeEvidence.md)

| Native scope | Primary array presence / scope word | Primary body IDs | Later array presence / body IDs | Null depth selector offset |
| --- | --- | --- | --- | ---: |
| All bodies | 0 / 0 | Empty | 1 / 101, 102 | 25,243 |
| Explicit A | 1 / 1 | 101 | 0 / empty | 24,918 |
| Explicit A+B | 1 / 1 | 101, 102 | 0 / empty | 25,247 |

Each primary selected-body row stores a raw owner word of −1. The later all-bodies rows carry the reached feature IDs 32 and 40. All three archives retain atom IDs 103 and 104 and two result choosers. Even in Explicit A, the B chooser carries Cut-side references while the native measurement shows its body remains unchanged. The parser retains both chooser surfaces and the distinct raw chooser state. Both body lists, the chooser records and the partition pairs have separate outputs.

The controls all have a depthless through-all extent and retain their raw partition state and unclassified start words. The native `AutoSelect` getter was false in all three cases. The typed replay now composes the configuration, profile, Boss and Cut readers on all three archives. It compares the saved selection and geometry participants with the independent native report, then checks the region identities against the reached body records. The earlier provisional replay also completed both saved archives. [Configuration replay](SolidWorksScopeConfiguration.md), [earlier provisional replay](../../Workers/SolidWorks/AutomaticScopeCutTerminal.md)

Run from the repository root with the retained report and parts in the same directory.

```text
python re/automation/SolidWorksScopeArchive.py /path/to/report.json --licensed-report-sha256 <report-sha256>
```

The [public adapter](SolidWorksScopedNeutral.md) uses the typed scope and independent body bindings to project both bodies and their saved history. It emits `sldprt.native_record_unresolved` for a recognized configuration when the required source joins fail. Paired conversion acceptance remains open.
