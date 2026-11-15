# Publish timeout cancellation once

When a queued application request reaches its deadline, the dispatcher publishes cancellation once before reporting the linked timeout. An existing acceptance fence keeps custody. Otherwise the dispatcher writes the quarantine. Closing the queue client then releases its dispatch lock. The cancellation reason keeps the existing archived-probe contract, and the timeout result identifies the exact request.

If cancellation publication fails, the application job returns `waiting_application`. The controller parks its resource, and the retained request occupies the endpoint spool. A linked timeout eligible for its own recovery checks requires successful cancellation publication.

The Windows process fixture checks settlement on the first attempt, original request custody, and parking when a filesystem conflict prevents cancellation publication. Hosted verification of this revision is pending.
