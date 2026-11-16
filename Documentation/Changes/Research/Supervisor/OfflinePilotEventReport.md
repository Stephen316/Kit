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

Add `--wait-timing` to measure the controller time from a recorded `waiting_application`, `waiting_evidence` or `waiting_ci` settlement to the same job's next claim within the fixed window. A new definition, invalidation or another settlement before the next claim ends that attribution. Waits with no next claim at the cutoff are reported separately, without a duration. The measurement includes any time spent queued after the job could proceed. It covers waits with explicit settlement events and does not reconstruct pending prerequisites that did not produce one.

Add `--open-wait-timing` to report the elapsed time from each still-open wait settlement to the last selected controller event. The report includes that event's ID and Unix timestamp, the trailing time from that event to the requested window end, and age totals grouped by the originating settlement outcome. The calculation uses only settlements recorded inside the selected window. A claim, invalidation, replacement or later settlement clears the original wait from the report. The trailing time carries no wait, idle or agent activity attribution. A window without selected events has no timing boundary.

Add `--carry-in-wait-timing` with `--after 0` to observe job waits already active at the start of the window. The section records the preceding event count, last event ID and canonical SHA-256 from the same fixed controller cutoff. Replay that prefix with the same window and `--through` bound. The option requires chronological events so a settlement or transition can be assigned to the correct side of the boundary.

Each wait outcome reports the number carried in, the next claims observed, the waits superseded by a definition change, invalidation or settlement, and the waits with no observed transition. Claim timing starts at the window boundary. A still-open age is shared by the waits of that outcome that remain at the last selected controller event. A window with no selected events has no observed age. This section leaves new settlements in the ordinary wait report and attributes no tail time or independent activity, acceptance or document gains.

The private inference supervisor's launch-bound replay found one inherited P04 evidence wait at event 126. Its prefix ended at event 185 and its last selected event was 198. The observed in-window age was 7,173.78 seconds, followed by 13,948.39 seconds with no selected controller event. The fixed replay left the ledger unchanged. The commissioning run and the two-week operating audit keep their own evidence requirements.

The first offline commissioning batch had one evidence wait 107.06 seconds before event 166, its last selected event. Its requested window extends another 66.34 seconds. The recovery batch had one evidence wait 37.81 seconds before event 79, with a trailing 2.97 seconds. Both are controller observations for the commissioning windows.

The retained Windows recovery run had one recorded evidence wait without a subsequent claim inside its 79-event cutoff. A disposable controller run confirmed timed application rearm, an evidence wait superseded by a new definition and a CI wait whose next claim was still unobserved. Both reports replayed with unchanged store bytes. [Recovery commissioning](OfflinePilotCommissioning.md)

The first replay used the [P03 affected depth run](../Inference/FusionDepthAffectedReplay.md). The retained store had 72 events and ten completed attempts. The longest path linked the signed-depth assessment to one archive rescan and totaled 5.37 attempt seconds. The command replayed the same bytes twice without changing the ledger. This measures the historical controller workload.

Hosted controller coverage exercises multiple pages, an event appended beyond the fixed cutoff, a parked claim, replay and byte-identical readback of the store.

At PR head `4285aea` and tested merge `e822910006afba1f68c4ad779aa64eae3367981b`, the dependency timing fixture completed its two-job chain and reproduced the report after a job revision. The Linux output-intake step passed, and Windows passed all 96 supervisor cases. The two-week unattended pilot still needs operating evidence. [Linux output intake](https://github.com/TryUniCAD/Kit/actions/runs/43804326178/job/133091614795), [Windows supervisor](https://github.com/TryUniCAD/Kit/actions/runs/43804326178/job/133091614740)
