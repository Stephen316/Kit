# Replay controller pre-pilot activity

Read a past time window from an existing private A03 store.

```sh
python3 re/automation/PilotActivity.py --store /absolute/path/ResearchStore \
  --from-unix 1730000000 --until-unix 1730003600
```

The first page fixes the last visible event ID for the whole report. Keep the reported start and end times, `after_event_id`, `through_event_id` and selected-event SHA-256. Use the same time bounds with `--after` and `--through` to replay that exact slice while the store continues recording work.

The report counts submissions, claims, settled outcomes, expired claims, resource transitions and recorded recovery activity. It includes explicit archived Fusion retry requests and recorded application timeout rearm events. Resource changes report availability. Record actor attribution separately. The digest binds the selected records while output contains aggregate counts and numeric evidence bounds.

Use this controller evidence alongside independently measured operator interventions, application activity, active agent time and accepted document gains when the offline pilot starts. A controller completion records a settled outcome. Independent conversion acceptance has its own evidence gates.

Use the [pinned private evidence report](PrivatePilotEvidence.md) to attach separately sourced intervention, interval and acceptance records to that fixed window.

Add `--dependency-timing` to measure the longest settled dependency chain by summed controller attempt time. The report starts at completed, nonprovisional settlement events in the selected window and follows the exact historical receipts declared as dependencies. Earlier ancestors contribute when those receipts bind the consumed job, result and timing. Each node's duration runs from its controller claim start to the receipt finish. The report gives path-wide attempt time, separate from readiness wait, retry time and independent application acceptance.

The first replay used the [P03 affected depth run](../Inference/FusionDepthAffectedReplay.md). The retained store had 72 events and ten completed attempts. The longest path linked the signed-depth assessment to one archive rescan and totaled 5.37 attempt seconds. The command replayed the same bytes twice without changing the ledger. This measures the historical controller workload.

Hosted controller coverage exercises multiple pages, an event appended beyond the fixed cutoff, a parked claim, replay and byte-identical readback of the store.
