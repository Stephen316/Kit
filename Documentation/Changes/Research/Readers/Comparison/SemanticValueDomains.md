# Semantic primitive value domains

The A06 graph projection now checks each primitive parameter's declared value kind before admitting observed equality.
`number` accepts integer or floating magnitudes, excluding booleans.
`integer` accepts only integers, excluding booleans.
`boolean` accepts booleans and `string` accepts strings.
Existing enum aliases retain the same domains.

A mismatched kind and value remains an unresolved `invalid_parameter_value_domain` observation.
The issue retains the declared kind, actual value and primitive type, supplied unit and evidence digest.
The graph keeps the original fields; it does not convert malformed values or invent replacements.
Identical malformed values on both sides cannot produce `equal_observed_graph`.
Unknown value kinds remain explicitly unresolved.

Length and angle normalization, finite-number guards, exact integer behavior, unsupported quantity/unit reporting and declared tolerance policy remain unchanged.
The shared model validator, codec and adapters are unchanged.
Every report retains unverified semantic qualification and unavailable native acceptance.

## Verification evidence

Dedicated process coverage creates independent valid documents with an additional owned primitive control, seals the serialized files and invokes the actual comparison command.
It covers wrong-domain observations repeated on both sides, valid nonunit values, enum aliases and an unknown kind.
The unresolved diagnostics must retain the supplied value and its evidence digest.
Static formatting, syntax, type and steering checks were performed.
Local tests, collection, SDK commands and native application execution were not run.
Hosted process execution and independent CAD acceptance remain required.
