# Fusion reset counts need historical attempt receipts

The current A03 job row changes when an input or definition is invalidated.
An application can already have completed a native request under an older
generation. Counting current completed rows can miss that execution.
Counting repeated acceptance of the same native request can inflate it.

Read the historical accepted attempt and validate its dispatch on the exact
process lifetime. Count each verified native request digest once.
[Fusion process completion evidence](../../../Changes/Research/Workers/FusionLifecycle/FusionResetEvidence.md)
