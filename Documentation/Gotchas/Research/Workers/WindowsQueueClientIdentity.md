# Windows queue client and supervisor process identities

The Windows queue records the PID and creation FILETIME of the Python process that submits a request. The supervisor receipt independently records the process it started and contained. A runner configured through a virtual environment launcher can yield two process identities in the same attempt.

All four licensed SOLIDWORKS rearm captures used the virtual environment's `Scripts/python.exe` runner. The queue client and supervisor receipt differed in both PID and creation time in every capture. The controller result, retained request bytes and listener recovery record consistently carried the same queue client identity. [Offline rearm evidence](../../../Changes/Research/Workers/SolidWorks/OfflineRearmEvidence.md)

Use the request hash, nonce and client identity to correlate queue records. Use the accepted attempt receipt and recorded session to bind the supervisor result. The listener and SOLIDWORKS launch ticket add separate identities for native recovery. Verifying ancestry between the launcher and the requesting process requires evidence collected from the live job object.
