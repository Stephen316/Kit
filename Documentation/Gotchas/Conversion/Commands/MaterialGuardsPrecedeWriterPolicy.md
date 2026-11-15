# Material support is checked before writer usability policy

`MakeFusionDoc` gives a constrained cuboid a physical material record. The SDK
registry checks typed-material support before staging or calling a writer. CATIA
does not implement the typed-material writer contract, so that input raises a
`ValueError` about density and color support before output-policy evaluation.

The CLI emits `error` and `message` for that refusal. Its nested `details` field
belongs to `UsabilityError` and is absent for an ordinary material `ValueError`.
Do not infer that every failed conversion has usability details.

Use a complete, qualified constrained rectangle without materials to exercise the
later CATIA usability refusal. Keep the cuboid case separately to verify material
rejection; do not strip materials from a solid or bypass the production guard.

See [the process-case correction](../../../Changes/Commands/WriterPolicyFixture.md)
and [registry ordering](../../../../src/convert/adapters/registry/RegistryWriteApi.py).
