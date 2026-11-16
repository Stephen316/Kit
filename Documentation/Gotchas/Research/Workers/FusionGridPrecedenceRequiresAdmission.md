# Fusion grid precedence depends on restart admission

An accepted Phase A can leave a retained restart fence while its exact Phase B
is queued. If an unrelated job claims the capacity-one resource first, the
application worker refuses the retained fence. Its waiting-application
settlement can make the installation unavailable to Phase B.

The optional restart reservation excludes unrelated jobs from the claim
selector until the saved Phase B evidence releases it. Apply the same
exclusion inside the requested-grid check. A queued but reserved-out requested
grid job otherwise still prevents an eligible standard-grid Phase B from
being selected.

[A03 restart reservation and hosted contention cases](../../../Changes/Research/Workers/FusionRestartResourceReservation.md)
