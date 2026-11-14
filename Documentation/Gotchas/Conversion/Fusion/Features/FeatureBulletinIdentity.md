# Journal bulletins must name one entity per object

## Expectation

A writer can store each version of a modified face, edge or vertex as its own journal entity.
Each delta state then creates or modifies the version that belongs to it.
Fusion opens such a journal, rolls it back and recomputes it correctly.

## Actual behavior

Fusion 2706.1.17 opened these journals, matched every rollback marker and recomputed them.
It terminated later while it disposed the closed documents.
The crash reports show `std::terminate` inside `HISTORY_STREAM::delete_delta_states`, called from `SMI_HISTORY::clear`.

| Kit work in the Fusion session | Crash point                                         |
| ------------------------------ | --------------------------------------------------- |
| Rejected-rule regressions      | `entity_data::set_history` in `delete_delta_states` |
| Hole acceptance                | `delete_delta_states` after the hole cases finished |
| Extrude acceptance             | `delete_delta_states` during the extrude cases      |

The 43 native controls that the Kit journal reader accepts all follow one identity rule.
The Fusion-saved exports of Kit documents follow it too.

| Bulletin                 | Native reference                                                       |
| ------------------------ | ---------------------------------------------------------------------- |
| Creation                 | The object entity                                                      |
| Modification, new side   | The same object entity                                                 |
| Modification, old side   | A backup that holds the earlier data and appears in no other bulletin  |
| Deletion                 | The object entity                                                      |

The object entity is live when the object survives to the final state.
It is a stored entity when the object is deleted.
Kit used the earlier version as the new side of the creation bulletin and as the old side of the next modification.
That version was therefore both a created entity and a backup.

## Workaround

Kit now writes the object entity on the new side of every creation and modification bulletin.
Backups keep their earlier data and appear only on the old side of one modification.
Pointers inside archived versions already named the object entity.

After this change, Fusion completed all five acceptance suites in one session and stayed running.
`BulletinRefs.py` in the part feature tests checks the rule for every authored case.
