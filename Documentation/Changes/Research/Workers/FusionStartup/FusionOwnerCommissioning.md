# Commission initial Fusion startup through the continuous owner

Start the [research supervisor](../../../../Reference/Research/ResearchSupervisor.md) in the signed-in macOS owner session. Queue the initial pair with `--owner-lifecycle` and store its durable receipt in the lifecycle owner's queue directory. Use the [pinned startup profile](../FusionStartupProvision.md) for that same installation.

```sh
python3 re/automation/ApplicationWorkers/FusionLifecycleOwner.py \
  --config /private/fusion/Supervisor.json \
  --installation /private/fusion/Installation.json \
  --lifecycle /private/fusion/Lifecycle.json \
  --queue-directory /private/fusion/Queue \
  --profile /private/fusion/StartupStage/startup-profile.json \
  --queue-receipt /private/fusion/Queue/InitialPair.json
```

The owner uses the same [cold-start custody](FusionOwnerColdStart.md) to prove initial startup and admit the selected Phase A. After admission, the same process starts the ordinary lifecycle loop immediately. Later pairs use their own queue receipts. A restart of the owner process rereads initial admission evidence through the same custody checks. An unresolved sealed physical launch stays parked, and the owner can observe an exact later receipt without initiating a second launch.

With `--once`, the owner reports just the initial startup disposition when the profile and receipt are supplied. Exit status 2 means the initial proof is still pending. The continuous mode advances later phases on its own. Start a lifecycle owner for an already commissioned installation by using the ordinary owner command.

The macOS cold-start fixture now resumes an interrupted launch through the continuous owner entry and checks its parked disposition when the launch receipt is withheld. The fixture uses disposable application peers. Hosted execution and a signed-in native witness are pending.
