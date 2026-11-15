# Fence application recovery with a resource hold epoch

A03 records a resource hold when its current supervisor owner settles a matching [queued SOLIDWORKS timeout](../Workers/SolidWorks/TimeoutProvenance.md).
The hold applies to the job's single capacity-one resource.
It binds the settle to that job, generation, fingerprint, attempt, execution ID and immutable failure receipt and result.
A03 records the corresponding `application_timeout_hold` event in the same transaction as the failed settlement and resource park.

A resource availability command advances its hold epoch even when it reaffirms the existing state.
A resource capacity change or another application failure also fences the earlier hold.
This lets a later recovery check distinguish the original timeout from a new decision to keep the resource unavailable.
Existing resource command responses and job admission rules retain their meaning.

The hold is a prerequisite for [supervised rearm](../Workers/SolidWorks/TimeoutRearm.md).
Rearm must match the current epoch, the exact failed attempt and verified archived spool evidence.
Remote Windows process verification covers the source timeout, durable hold and an explicit reaffirmation of unavailability.
