# Accepted Fusion output may still hold its installation

A03 can accept a Phase B result before the acknowledgement worker removes the
application spool. A failed acknowledgement future can disappear from the
supervisor's live queue while its durable intent remains. Another claim at
that point can hit the retained acceptance fence and park the installation.

Keep the exact reservation until the endpoint clears and the supervisor
retires the bound intent. Resume an uncertain acknowledgement through the
same durable result and request. The receiver can verify that it already
cleaned up without touching the next spool.
[Phase B acknowledgement recovery](../../../Changes/Research/Workers/FusionLifecycle/FusionPhaseBAcknowledgement.md)
