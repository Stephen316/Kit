# Native compute can pause in an informational dialog

A dispatched Fusion Python call can stop advancing while the process remains responsive and nearly idle. In the mesh-shell control, `Design.computeAll()` stopped while Fusion showed an information dialog. This was not a failed persistence decode or a completed computation.

The observed dialog was titled “About Your Fusion Documents” and explained editable-document limits. Clicking its existing “Ok. Got it.” button allowed the same call to continue. No subscription, entitlement, editable-document state or access setting was changed. Both source/reconstructed mesh candidates subsequently passed native rebuild, edit, save and reopen.

When a native call stalls, preserve its checkpoint and look for an open dialog before retrying the script or terminating the application. A timeout alone does not identify a malformed file. [The bounded runtime evidence](../../../../../re/Fusion/LocalOracle/ParaMesh/RuntimeDialog.json) records the observed dialog and action; [native acceptance](../../../../../re/Fusion/LocalOracle/ParaMesh/NativeAcceptance.json) records the completed result.
