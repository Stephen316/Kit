# A missing Fusion PID leaves automatic quit custody unresolved

## Expectation

An authorized replacement clears the restart fence once it verifies its own startup and the prior process's exit.

## Actual behavior

The original startup gate accepted a new trusted host after the prior PID disappeared. The prior process can also disappear after the armed observer timed out or lost its watch. A separately started process could clear the fence while that automatic quit remained unresolved.

## Workaround

Retain the automatic handoff's hold. The replacement must have an exact exit receipt and a verified launch receipt for the current process before startup clears the fence. When the old process remains live, the owner can use an independent operator-directed watch to obtain an exact exit receipt. [Guarded Cocoa quit](../../../Changes/Research/Workers/FusionArmedCocoaQuit.md)
