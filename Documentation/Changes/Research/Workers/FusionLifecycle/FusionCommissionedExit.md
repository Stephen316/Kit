# Retain the commissioned Fusion process exit

The continuous macOS lifecycle owner can keep a Darwin kernel watch for the
exact initial process it commissioned. This uses the same owner command and
startup profile. Once the cold-start admission is durable, the owner verifies
the associated launch and startup receipts, source pins, bundle and exact
process identity. A nonblocking kernel watch stays armed across normal
reconciliation.

The exit receipt names the admitted initial job, generation, fingerprint, and
launch, bootstrap and installation evidence. It identifies a matching
scheduled quit, unresolved quit custody, or an event outside the owner's
scheduled quit. None of these dispositions assert a process exit cause.

A replacement owner invocation re-arms a still-live exact peer. With a
missing process and no persisted observation it reports an unobserved exit.
A fresh kernel watch starts only after successful registration. There is no
continuous observation claim across an observer outage. The command retains
its existing one-reconciliation behavior under `--once`. This evidence
carries no automatic restart or retry admission. Later replacement epochs
still require a separate verified watch.

The hosted cold-start witness uses a disposable AppKit process, restarts the
owner while the peer is live, and verifies which observer recorded the exact
exit. It also checks that hiding the durable exit receipt cannot turn
later process absence into a verified exit. It passed at PR head `d0288d10`
on tested merge `6ee63ca70913eac551d8e780b85d26437e0ca98d`. The macOS suite
reported 164 passes, two skips and one pilot timing fixture failure. The
fixture had omitted the controller's required settlement reason. A signed-in
Fusion replacement and its preclaim healthy control remain open.
[Hosted macOS result](https://github.com/TryUniCAD/Kit/actions/runs/43801915215/job/133084019077)
