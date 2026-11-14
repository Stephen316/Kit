# A drawing that names absent objects can crash the drawing engine

Fusion 2706.1.17 does not check that each DWG handle names a present object.
The drawing engine crashed while it opened `G1FreshHandles`, a Kit-built variant that named absent objects.

| Observation                             | Value                                                  |
| --------------------------------------- | ------------------------------------------------------ |
| Time from open to engine crash          | About 10.5 minutes                                     |
| Script stage after the crash            | DWG export, which never returned                       |
| Absent handle in the `SOURCEMGR` xrecord | 1                                                     |
| Absent view handles in `AUTO_VIEW_XDATA` | 3                                                     |
| Recovery                                | Fusion was stopped and relaunched                      |

The single variant does not show which absent handle caused the crash.
`G2FreshClean`, built the same way, was quarantined and never opened.

Handles hide in places that a typed object graph does not follow.

| Place                                  | Example                                                  |
| -------------------------------------- | -------------------------------------------------------- |
| Xrecord group codes 320 to 369         | `ACDB_RECOMPOSE_DATA` names a dimension action body      |
| Extended data group 1005               | Handle text in an application's extended data            |
| Extended data group 1071 values        | `AUTO_VIEW_XDATA` stores view handles as 32-bit integers |

Kit's authoring checks every typed reference, and it builds the integer handle lists from its own objects.
The research builders refuse a variant when any typed or numeric handle names an absent object.
Open a variant with absent handles only as the last case of a guarded run.
