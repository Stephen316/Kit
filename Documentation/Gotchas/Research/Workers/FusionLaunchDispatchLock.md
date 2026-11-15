# Release the dispatch lock before requesting a Fusion launch

The owner needs the dispatch lock when confirming the old restart fence and sealing a replacement launch request. The verified replacement add-in can release that fence before LaunchServices returns its callback. Phase B observes the cleared fence, then tries to acquire the dispatch lock without waiting. An owner still holding it can cause Phase B to park while the exact replacement starts successfully.

Seal the one-use launch request while holding the dispatch lock, then release it before invoking LaunchServices. A separate private owner lock serializes launch requests. The provider checks the original fence bytes immediately before it requests the launch. Phase B can then use the ordinary queue once the new add-in verifies its startup. [Owner replacement launch](../../../Changes/Research/Workers/FusionReplacementLaunch.md), [Phase B fence handling](../../../Changes/Research/Workers/FusionPhaseQueue.md)

The race follows from the existing nonblocking queue acquisition and trusted startup fence transition. The hosted disposable bundle fixture exercises the native launch boundary separately from a licensed Phase B run.
