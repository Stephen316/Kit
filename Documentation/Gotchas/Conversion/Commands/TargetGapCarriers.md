# Carrier refusal can still permit intrinsic target limitations

The SDK's existing `allow_carrier=False` policy permits reported carrier transfers whose reason is `target_unsupported` when the writer otherwise reports usable, loadable output.
For example, FreeCAD preserves multiple neutral configurations in its carrier data and reports that intrinsic target limitation.
The option does not mean that every capability is represented natively.

The CLI additionally enables `require_native_transfers=True`.
The checked write then refuses every non-native transfer, including mixed transfers and target limitations, before publishing staged output.
SDK callers can request the same policy through `WriteDocument` `InputValues`; the default remains unchanged.

See [the policy change](../../../Changes/Commands/NativeTransferPolicy.md).
