# Read controller event windows

Pilot observers can read the controller's committed event history in ascending pages of up to 100 events. The first page records an inclusive upper event ID. Reusing that bound across pages gives an observer the same append-only prefix even as the controller records new work. The default `events` command continues to return the most recent 100 rows in descending order.

```sh
python3 re/automation/Controller.py --store /tmp/KitResearchState events --after 0
```

The response includes `after`, `through`, `next_after`, and the event rows. While `next_after` has a value, pass it as `--after` and pass the original `through` as `--through`. When the window is exhausted, use that `through` as `--after` to open the next window. Event IDs are scoped to the same controller store. Keep the exported pages, store provenance, and controller checkout identity together when collecting pilot evidence.

Window reads use a read-only SQLite transaction. They preserve the owner fence when a supervised caller supplies its owner token. A window needs an initialized store. It creates no ledger, and it reads only already committed events. [SQLite read-only mode](https://www.sqlite.org/c3ref/open.html), [SQLite read transactions](https://www.sqlite.org/lang_transaction.html)

The feed supplies recorded claims, finishes, outcomes and recovery transitions. Readiness, active agent time, independent CAD acceptance, and operator interventions still need their own observations in an A15 pilot. [Pilot requirements](../../../Reference/Research/AutomationPlan.md#delivery-and-forecast)

The existing controller process selection now exercises an empty store, a window longer than 100 rows, new activity between pages, the legacy event view, cursor refusal, stale owner rejection, and preservation of the existing database bytes. Remote verification is pending.
