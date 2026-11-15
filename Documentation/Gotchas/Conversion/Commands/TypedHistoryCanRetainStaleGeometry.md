# Typed history can retain geometry that its operations do not produce

Two active extrusion identities do not prove the result of a Boolean operation.
A cut between coincident operands can retain an unrelated nonempty B-rep in a neutral document.
Likewise, changing driving controls can leave stored B-rep coordinates unchanged while identity and reference validation still pass.

The CLI now requires geometry to match the SDK's existing authoring or native-state regeneration contract.
Generic Boolean and bound-scale models without such a contract remain available for inspection.
The gate reuses SDK validation instead of inventing a Boolean evaluator.
Temporary comparison snapshots ignore only nonsemantic provenance/attribute bags and document source/root metadata; all geometry, controls, names, and units remain checked.
The original document is preserved for the selected writer.

See [the SDK geometry contract change](../../../Changes/Commands/SdkGeometryContract.md).
