# Resolved placement does not establish parametric assembly history

An assembly graph can resolve each component, store typed transforms and mates,
and retain qualified child geometry without a root feature timeline or a
qualified reconstruction contract for its placements. The interchange writer
can serialize that graph; native capability reports do not prove a live assembly
feature history.

The CLI refuses assemblies with placed instances, at any document depth, until
placement history can be qualified. Empty local assemblies also require model
history under [the complete model guard](../../../Changes/Commands/ParametricModelGuard.md). Use `kit decode` or deterministic
`kit research` for inspection. Converting child geometry independently does not
establish acceptance for the assembled model.

See [the guard change](../../../Changes/Commands/AssemblyPlacementGuard.md).
