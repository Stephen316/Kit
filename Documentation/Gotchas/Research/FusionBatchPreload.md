# Per-file limits do not bound a preloaded batch

A 256 MiB input limit can appear to bound a decoder's source allocation.
Preloading 1000 inputs retains up to 250 GiB before decoding starts.
The earlier Fusion research batch loop retained this complete list.

Load and validate one committed payload immediately before its decode.
Release it before the next load, rather than retaining the previous iteration's bytes during allocation.
Keep staging private until the whole batch passes pin and source-stability checks.
A late pin failure must remove all staged output.
See [the repair](../../Changes/Research/FusionBatchSourceLifetime.md).
