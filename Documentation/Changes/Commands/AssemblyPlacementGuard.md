# Keep unqualified assembly placement inspectable

`kit convert` refuses document graphs containing placed assembly instances with
`UnqualifiedAssembly`, including nested placements. Resolved component sources,
typed mates, and qualified child geometry do not establish full parametric
placement history for the assembly owner. No existing SDK contract qualifies
that history, so the CLI conservatively refuses these assemblies for every
destination. The SDK and deterministic research tools are unchanged.

Validation still checks descendants for opaque records, missing feature history,
retained payloads, and invalid geometry before placement qualification. This keeps
specific inspection diagnostics available. Independently qualified standalone
documents remain eligible. Empty local assemblies also require model history;
see [the complete model guard](ParametricModelGuard.md).

Remote process cases cover resolved/provenance references, root/subassembly
owners, nested documents, and absent/existing destinations. Existing nested
success cases now require explicit refusal and successful decoding; standalone
positive coverage remains. No local tests or decoding ran. Static validation and
exact-head remote CI evidence are recorded in PR #119.

See [the assembly-history gotcha](../../Gotchas/Conversion/Commands/PlacedInstancesAreNotParametricHistory.md).
