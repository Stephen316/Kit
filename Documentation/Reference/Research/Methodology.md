# Reverse engineering method

## Purpose and boundary

This reference describes isolated research into CAD formats.
It does not authorize vendor automation in production conversion.
The original research record is [re/Methodology.md](../../../re/Methodology.md).

## Research sequence

| Phase                 | Action                              | Required evidence                           |
| --------------------- | ----------------------------------- | ------------------------------------------- |
| Container             | Identify streams and framing        | File hashes, boundaries, and signatures     |
| Oracle                | Establish quantitative measurements | Healthy controls and measured outputs       |
| Differential samples  | Vary one property                   | Sample identities and exact differences     |
| Runtime trace         | Observe record reads and writes     | Binary build, addresses, and trace spans    |
| Decompilation         | Identify types and branches         | Function identity and decoded rule          |
| Native implementation | Encode the understood grammar       | Integration and target-application evidence |

The sequence reduces unsupported assumptions.
It does not make every inference correct.
Record refuted hypotheses as well as successful findings.

## Differential samples

Create repeat saves to identify timestamps and other unrelated differences.
Create feature-count ladders to identify repeated structures.
Exercise both values of a boolean field.
Change one controlled parameter at a time.
Keep vendor-authored inputs distinct from generated candidates.

A byte difference identifies a correlation.
A decoded rule and measured behavior establish stronger evidence.
Do not infer a universal offset from a single pair of files.

## Runtime and static evidence

Runtime traces reveal buffer positions, record boundaries, and reference indices.
Decompilation reveals field types, version branches, and enum handling.
Record the exact binary hash and build for each address.
An address from another build can identify unrelated code.

Symbolic re-emission can check a proposed record segmentation.
Byte identity supports the exercised case.
It does not prove every branch or target-application acceptance.

## Confidence register

| Status    | Meaning                                                                                     |
| --------- | ------------------------------------------------------------------------------------------- |
| Confirmed | The rule is decompiled and reproduces a real traced span, corpus record, or measured number |
| Partial   | The rule is decompiled, but no available observation exercises it                           |
| Not found | The rule has not been found                                                                 |

Record the status next to the field or feature family.
Do not replace an unknown field with recorded donor bytes in production output.

## Caches and derived values

Separate authored parameters from derived caches.
Verify regeneration behavior for each cache and vendor build.
Do not assume that a stale value is harmless.
Do not write an approximate value as a substitute for a missing derivation.

## Promote research into product code

1. Identify the confirmed grammar and source evidence.
2. Implement the parser or writer from that grammar.
3. Remove dependencies on donor fixtures and vendor runtimes.
4. Add integration coverage at the conversion boundary.
5. Obtain remote product acceptance evidence.
6. Document supported inputs and unresolved limits.

The `re/` exemption applies to research organization and code standards.
It does not establish production readiness.

## Related information

- [Research tools](Tooling.md)
- [Oracle evidence](Oracles.md)
- [Product verification](../Operations/Testing.md)
