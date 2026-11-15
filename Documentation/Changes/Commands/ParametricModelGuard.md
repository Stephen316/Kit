# Require complete model history and driven solid profiles

`kit convert` now requires feature history in every document, including documents
containing only parameters or an empty assembly. Parameters alone do not supply
model history. Structural and geometry diagnostics are still evaluated before
the final history check. Inspection remains available through `kit decode` and
the deterministic research tools.

Every sketch must have active driving constraints bound to its declared parameter
IDs, including sketches used by solid generators. A length-driven cylinder with
a literal undimensioned radius does not qualify its profile. The existing SDK
regeneration comparison remains required; dimension tags cannot qualify geometry
that disagrees with that contract. Dimension-driven constrained cuboids and
constrained rectangle sketches remain eligible. Standalone native roundtrip
coverage uses a constrained cuboid.

Remote process cases cover undriven circle and rectangle solid profiles, parameter
documents with absent/existing destinations, and the existing nested/refusal
matrix. No local tests or decoding ran. Static formatting, typing, steering,
rationale, path, and whitespace evidence and exact-head CI results are recorded
in PR #119. No target-application acceptance is claimed.

See [undriven profiles](../../Gotchas/Conversion/Commands/UndimensionedProfilesAreStatic.md)
and [parameter-only documents](../../Gotchas/Conversion/Commands/ParametersDoNotSupplyHistory.md).
