# Replay controller pre-pilot activity

Read a past time window from an existing private A03 store.

```sh
python3 re/automation/PilotActivity.py --store /absolute/path/ResearchStore \
  --from-unix 1730000000 --until-unix 1730003600
```

The first page fixes the last visible event ID for the whole report. Keep the reported start and end times, `after_event_id`, `through_event_id` and selected-event SHA-256. Use the same time bounds with `--after` and `--through` to replay that exact slice while the store continues recording work.

The report counts submissions, claims, settled outcomes, expired claims, resource transitions and recorded recovery activity. It includes explicit archived Fusion retry requests and recorded application timeout rearm events. Resource changes report availability. Record actor attribution separately. The digest binds the selected records while output contains aggregate counts and numeric evidence bounds.

Use this controller evidence alongside independently measured operator interventions, application activity, active agent time and accepted document gains when the offline pilot starts. A controller completion records a settled outcome. Independent conversion acceptance has its own evidence gates.

Hosted controller coverage exercises multiple pages, an event appended beyond the fixed cutoff, a parked claim, replay and byte-identical readback of the store.
