# Observe one owner-launched Fusion archive replacement

Add `--launch-archived-replacement` when starting the continuous owner with
its existing commissioning profile and queue receipt. This enables one
replacement launch for the exact first hostless timeout after the
commissioned native exit, original archive and current A03 generation have
been verified. The owner seals one request for the pinned physical bundle
and the unique archive challenge. An existing provider request with a
missing observation stays parked.

The commissioning profile must pin the revision that contains this provider
mode and the installed vendor-startup add-in. For Fusion, the existing
signed-in macOS owner session supplies the startup context.

The reviewed LaunchServices provider checks the archive and preflight pins,
empty endpoint and process roster. Through a private process pipe it waits
for the owner to revalidate the parked controller snapshot. The owner holds
that read snapshot only through the asynchronous launch submission. The
endpoint lock keeps the existing explicit retry from racing with launch,
and the new add-in can acquire its own host lock.
[Apple LaunchServices application submission](https://developer.apple.com/documentation/appkit/nsworkspace/openapplication(at:configuration:completionhandler:))

The durable process receipt identifies the exact fresh UID, PID, birth and
bundle. The owner separately obtains the pinned vendor-startup bootstrap
reply bound to that same installed process and archive launch challenge.
`startup_verified_control_pending` records that proof while A03 remains
parked. The healthy control and second attempt still require their own
verified admission.

The separately opted-in [archive control](FusionArchivedControl.md) takes
the next observation on this exact startup peer.

The hosted case uses a disposable AppKit app and the actual pinned
bootstrap callback while exercising the existing A03 archive. It checks the
fresh replacement process, the bound startup response and recovery when the
process receipt is withheld. Hosted execution and a signed-in Fusion
replacement with a real healthy control remain pending.
