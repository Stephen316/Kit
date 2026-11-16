# Portable semantic graph comparison

## Behavior

The research comparator reads two pinned `CadDocument` JSON files through the existing codec and document validator.
It constructs explicit ownership and reference graphs from their typed records.
Record identities and display labels remain evidence, rather than universal correspondence keys.

The matcher compares record kinds, fields, reference roles, duplicate references and already matched neighbors.
It accepts unique reciprocal correspondences and retains unresolved alternatives.
Candidate, field-work and evidence budgets bound the matching work.
Exhausted groups remain explicitly incomplete.
They are never matched by traversal order.

Declared geometry units and typed parameter units produce separate normalization paths.
Lengths, angles, areas, volumes and dimensionless directions use their own caller-supplied absolute tolerances.
Counts, booleans and exact fields remain exact.
Material fields, suppression, expressions, configuration overrides, feature order and dependency references remain observable.

The report separates observed field differences, ambiguous correspondence and unresolved source domains.
It records both input hashes, the tolerance-profile hash and source identity digests.
Native bytes, native-only records, missing feature definitions and unclassified extensions cannot become an equality success.
This includes [source and provenance extension bags](../../../../Gotchas/Conversion/ProvenanceExtensionBags.md) and uncertain provenance confidence.
Assemblies, full boundary representations, payloads, meshes and reader diagnostics require their own independent comparison and remain explicit unresolved domains.

Inline and parameter-linked feature definitions retain their distinct typed representations.
The tool does not infer equivalent driving relationships from equal evaluated values.
Selected contour order and constraint operand order remain observable.
It does not silently rewrite orientation or expressions to make native readers agree.

## Use and limits

See the [comparison guide](../../../../Reference/Research/SemanticComparison.md) for the command, required pins, limits and exit codes.
No public adapter, serializer registration or neutral schema changes.
An equal observed graph does not establish independent source coverage, portable writer support or target application acceptance.
Every report retains unverified semantic qualification and unavailable native acceptance.
The [step register](../../../../Reference/Research/AutomationSteps.md) retains the qualification dependencies.

## Verification evidence

Source inspection used the existing model dataclasses, quantity bindings, wire codec and relationship validator.
The new process coverage constructs independent typed documents, serializes them, and invokes the actual standalone comparison command.
It covers renamed identities, explicit unit conversion, meaningful field/reference changes, symmetric ambiguity, unresolved evidence and input refusals.
Candidate exhaustion remains an incomplete result.
Local tests and collection were not run.
Static syntax and formatting checks ran during implementation.
Hosted execution and independently qualified paired evaluation remain required.
