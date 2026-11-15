# Installed CLI modules can differ from the research checkout SDK

An installed CLI and a selected checkout can contain different SDK revisions.
Importing a research reader into the CLI process can reuse the installed `convert` and `interchange` modules.
That can mix checkout fingerprints with another SDK's behavior.

The launcher starts the selected checkout script in a fresh interpreter.
Linux and macOS replace the launcher process; Windows waits for the child and forwards its exit status.
Those scripts explicitly load their own checkout's `src/` tree.
The wrapper forwards arguments and artifacts rather than importing research modules or rebuilding receipts.
Remote cases compare direct and CLI artifacts byte for byte on the selected checkout.
The standalone compatibility suite uses the installed CLI and a separately pinned research checkout, checking receipt revision and SDK-source digest.
Its accepted-head remote result is required before claiming verified cross-checkout compatibility.
See [the research CLI](../../Tasks/ResearchCommandLine.md).
