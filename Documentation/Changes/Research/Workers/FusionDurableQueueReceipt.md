# Persist and recover the Fusion queue receipt

On macOS, Linux or Windows, add `--receipt` with an absolute private receipt path to the [Fusion phase queue](FusionPhaseQueue.md) command. Use an existing directory that only the owner can access. The command creates owner-private records and prints its usual receipt on stdout. The [Windows receipt entry](Windows/WindowsFusionQueueReceipts.md) describes its protected directory/file handles and path-name restrictions.

The command seals a private sibling `.QueueReceipt.json.intent.json` with the exact store, run, receipt and both definition digests before submitting the pair. It publishes the receipt after verifying the committed plan binding and both job definitions. The receipt uses the existing schema and remains usable by the phase audit and owner restart commands.

If submission was interrupted, verify the committed pair and publish the missing receipt with the same supervisor configuration.

```sh
python3 re/automation/ApplicationWorkers/QueueFusionPhases.py \
  --config /absolute/private/Supervisor.json \
  --recover-receipt /absolute/private/QueueReceipt.json
```

Recovery reads the bound plan from A03 and checks both exact definitions in a read-only snapshot. Keep the sibling intent. Recovery needs no original plan path and makes no new A03 submission. If the transaction never committed, repeat the original submission with its original arguments and receipt path. A conflicting file, a changed binding or an incomplete pair fails without replacing a receipt. [Interrupted publication](../../../Gotchas/Research/Workers/FusionQueueCommitPrecedesReceipt.md)

The existing stdout-only queue command remains available on all three platforms. The hosted boundary fixture interrupts the real queue process before submission and after the ledger commit, then exercises recovery and conflicting replay. It passed in the 154-case macOS suite at PR head `3cd136ad` and tested merge `e1fa7f1d`. That observation does not verify the later Windows expansion. [Hosted macOS suite](https://github.com/TryUniCAD/Kit/actions/runs/43781577583/job/133019772047)
