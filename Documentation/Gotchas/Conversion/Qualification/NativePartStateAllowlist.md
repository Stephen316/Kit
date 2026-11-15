# Part codec support does not imply public authoring state support

## Expectation

A family specification accepted by the low-level Fusion codec can also become a public `fusion.authoring` document, including its historical native-tagged move step.

## Actual behavior

The [native qualification gate at `6e2da255`](https://github.com/TryUniCAD/Kit/actions/runs/43673027349/job/132687037643) passed 323 cases and failed three before reaching the write guard. `MakeFusionDoc` could not encode `ExtrudeSpec` into its semantic state.
The fixed state type inventory does not contain the family feature and curve types required by that fixture. Low-level archive generation and body readback exercise a different path.

## Workaround

Use the existing cuboid contract for the public positive file case. Keep the part-family codec file and its explicit public state refusal as separate evidence.
Reject explicit native feature tags at public writes; neither an authoring metadata label nor low-level codec support independently qualifies them.
Do not widen the state allowlist to silence the fixture failure. A future supported public part contract needs its own independent qualification.
See [native semantic write qualification](../../../Changes/Research/Readers/NativeSemanticWriteQualification.md).
