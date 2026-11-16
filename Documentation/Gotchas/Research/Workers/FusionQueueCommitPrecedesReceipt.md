# An interrupted Fusion queue can leave a committed pair

## Expectation

A missing queue receipt suggests that the process did not finish submitting the phase pair.

## Actual behavior

A03 commits both job definitions before the command can publish the receipt or return it on stdout. A process interruption in that interval can leave the exact pair committed with no visible receipt.

## Workaround

Keep the submission's private sibling intent. Run receipt recovery to verify both definitions and their bound plan without changing the controller. Keep the original run label if the transaction did not commit and needs to be submitted again. [Durable Fusion queue receipt](../../../Changes/Research/Workers/FusionDurableQueueReceipt.md)
