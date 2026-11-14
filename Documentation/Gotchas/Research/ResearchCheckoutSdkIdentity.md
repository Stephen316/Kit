# Installed CLI modules can differ from the research checkout SDK

An installed CLI and a selected checkout can contain different SDK revisions.
Importing a research reader into the CLI process can reuse the installed `convert` and `interchange` modules.
That can mix checkout fingerprints with another SDK's behavior.

The launcher replaces its process with the selected checkout script in a fresh interpreter.
Those scripts explicitly load their own checkout's `src/` tree.
The wrapper forwards arguments and artifacts rather than importing research modules or rebuilding receipts.
Remote cases compare direct and CLI artifacts byte for byte on the selected checkout.
Cross-checkout execution is supported by this process boundary; separate cross-checkout runtime evidence remains unavailable.
See [the research CLI](../../Tasks/ResearchCommandLine.md).
