# Stale members and grouped adaptive capacity

## Expectation

A physical group stop with an observed memory limit or deadline can inform the pool's adaptive limit when the controller accepts a current attempt.

## Actual behavior

An input change can invalidate every member after the supervisor has stopped the process.
The stop remains observable, while the controller rejects the late settlements.
Earlier grouped accounting treated those responses as current because it assigned the same freshness status to every physical group.

## Workaround

Use the controller's validated member responses to determine group freshness.
Count the physical group once if at least one member's settlement is current.
Learn a group memory sample only after the controller accepts every completed member.

See [the change entry and hosted verification status](../../../Changes/Research/Supervisor/GroupedAdaptiveSettlement.md).
