# A failed collector can leave the owned SOLIDWORKS process running

## Expectation

The supervised collector returns an error after finishing native cleanup.

## Actual behavior

The P04 collector requires an empty document set before it asks SOLIDWORKS to exit. If closing a scratch document fails, the collector can report failure while the process it attached to remains alive. The PowerShell wrapper exits nonzero and the listener quarantines the request.

## Workaround

Keep the exact launch handle until the listener has evaluated the result. On a dedicated scratch listener with the failure-recovery option, verify the immutable ownership ticket and the live handle before attempting bounded termination. Inspect the retained quarantine when custody or exit cannot be established. [Collector failure recovery](../../../Changes/Research/Workers/SolidWorks/CollectorFailure.md)
