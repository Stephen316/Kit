# Fusion main-thread availability

## Expectation

A recent add-in status file proves Fusion can accept a native capture request.
An application script can also own shutdown simply because it can queue work.

## Actual behavior

Fusion's [Application API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Application.htm)
queues custom events for the main thread when the application is idle. Firing an
event does not synchronously execute its handler. A background heartbeat therefore
does not prove main-thread responsiveness or a healthy document/control state.

The documented application object provides no quit/restart member. A dispatcher
must not invent text commands or kill an application that its process supervisor
does not own. The legacy capture add-in also accepts only `GenerateFusion.py`;
prepared phase launcher scripts do not satisfy that legacy script restriction.

## Workaround

Use the versioned local dispatch counterpart, which services a fresh challenge on
the main thread, measures the pinned healthy control and invokes the fixed pinned
fresh-phase helper entry point. Keep application files in an installation-owned
private spool until the application responds; session cleanup can otherwise remove
paths while an external application is still using them.

Fence the installation on timeout and emit an identity-bound restart handoff after
phase A. Require the external owner to restart the application and prove the old
process exited. Late output remains unaccepted. Source hashes prove which code was
loaded; they do not establish native semantic qualification.

The [dispatch change](../../../Changes/Research/Workers/LocalApplicationDispatch.md)
records configuration, process coverage and remaining restart/native-host gaps.
