# Windows application queue transport

The local research application protocol can hold its endpoint owner and client locks on Windows. This supplies a transport prerequisite for A08c and A08e. A client parks its job when the configured application is unavailable. [Local application dispatcher](LocalApplicationDispatch.md)

Use a local volume and an owner private installation endpoint. The Windows endpoint locks hold exclusive file handles and keep their parent directories open. The lock file must be a singly linked regular file outside any reparse point. A competing process receives a lock failure before acquiring the endpoint. The operating system releases custody when the owning handle closes. Linux and macOS retain their existing file locking behavior. [Windows file share modes](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)

Request and response identities pair the actual process ID with exact Windows creation time. The transport shares the supervisor's identity reader. It checks the response against the live host and binds it to the request nonce, installation, revision, provider, and request hash.

The restart and acceptance fences retain a completed spool until controller acceptance. A restarted host parks requests against that installation. Output uses the protocol's immutable reads and exclusive publication. The external owner controls the licensed application lifecycle. [Durable worker output](DurableWorkerOutputs.md)

The Windows research selection includes live host and client process scenarios for request exchange, both forms of contention, refusal of a multiply linked lock, normal fixture shutdown, and acceptance retention after host restart. At `cdf53e1f`, the job passed all 29 selected process cases. [Windows research job](https://github.com/TryUniCAD/Kit/actions/runs/43693322495/job/132748412625)

The SOLIDWORKS listener runs the pinned P04 readback as a queued operation on a licensed Windows host. Recovery evidence for hung or lost COM calls remains open. [Queued SOLIDWORKS readback](SolidWorksQueuedReadback.md)
