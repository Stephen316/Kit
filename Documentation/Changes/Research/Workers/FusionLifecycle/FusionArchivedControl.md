# Measure archived Fusion replacement health before a second claim

Add `--measure-archived-replacement` to the continuing Fusion lifecycle
owner that already opts into
[archive replacement launch](FusionArchivedReplacement.md). Use the same
commissioning profile and exact queued pair. After the new peer produces
its bound vendor-startup receipt, the owner publishes one private request
for the parked archive.

The pinned startup handler accepts that request only on the exact
replacement main thread while the requesting peer holds dispatch custody.
It checks that the application has finished startup, has no active jobs,
and has no open or active document. It reserves the request durably and
runs the existing pinned healthy control. That control imports the
committed control archive, recomputes it, measures the expected body and
volume, and closes the control document without saving. No ordinary
application grant is written.
[Autodesk Fusion application event and state API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Application.htm),
[Autodesk Fusion archive import API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_ImportManager.htm).

The owner uses its existing wait budget up to 30 seconds. A request with
no verifiable response remains parked and is never republished. Recovery
can verify the retained result independently of the waiting process.
`control_verified_admission_pending` reports the control receipt digest.
The resource and second A03 attempt remain parked. A later admission
would require current proof and a separate exact controller transaction.
Once automatic control custody is durable for that archive, the older
manual retry command defers to its owner.
The owner can separately opt into
[transactional retry admission](FusionArchivedRetryAdmission.md).

The hosted process case uses a disposable AppKit app and a vendor API
stand-in to drive the real pinned control code and committed input. It
checks import, recompute, no-save close, one-shot reservation and response
recovery, without treating the observed data as licensed Fusion results.
The macOS supervisor verified this control and the optional retry admission
at `f0962377`. Signed-in native Fusion control evidence remains pending.
[Hosted macOS result](https://github.com/TryUniCAD/Kit/actions/runs/43847585169/job/133231532025)
