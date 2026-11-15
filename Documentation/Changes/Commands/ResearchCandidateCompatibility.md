# Verify the installed research CLI against the workflow candidate

The Linux and Windows research CLI compatibility jobs use the exact GitHub candidate for the installed CLI source and a separate `ResearchCheckout` for its research tools. The research checkout retains full Git history so the readers and corpus can resolve historical object pins. A merge-queue shard checks out the same candidate tools when its test plan includes research CLI cases.

The compatibility fixtures check both local Git revisions against the workflow SHA before selecting the research root. The supervisor scenario launches its configured runner from that root. The launcher signal scenarios use a separate disposable script to hold the actual child startup boundary. Reader cases compare direct and CLI output and check the selected SDK's receipt provenance.

Follow [the research CLI procedure](../../Tasks/ResearchCommandLine.md) for a working installation. Exact-candidate hosted results are pending.
