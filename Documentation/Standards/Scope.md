# Documentation standards and scope

## Purpose

This page identifies the standards used for the Kit documentation.
It separates project rules from evidence of standards conformance.
The information owner is the Kit maintainer role.
The document version is the Git revision that contains this page.

## Document set

The maintained document set consists of `README.md` and the Markdown pages in `Documentation/`.
It includes task guides, reference pages, maintenance procedures, change records, and the gotchas log.
The [documentation index](../Index.md) provides navigation for the complete set.

Source identifiers, commands, error strings, and format names retain their exact spelling.
License notices retain their legal text.
Historical source quotations and recorded measurements retain their original meaning.
These items do not authorize unrestricted language in surrounding prose.

Research records in `re/` are evidence inputs, not instructions for product use.
The preserved standards archive is a historical source with byte verification in CI.
Do not rewrite either source to make a documentation check pass.
The [repository instructions](../../AGENTS.md) continue to control contributions.

## Standards register

The register uses public publisher information checked on 2026-11-11.
An edition in development does not replace a published edition.

| Standard           | Edition used        | Subject                                                     | Public source                                                                    |
| ------------------ | ------------------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------- |
| ASD-STE100         | Issue 9, 2025-01-15 | Controlled technical language                               | [ASD publication](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf) |
| ISO/IEC/IEEE 26511 | 2018                | Management of information for users                         | [ISO catalogue](https://www.iso.org/standard/70879.html)                         |
| ISO/IEC/IEEE 26512 | 2026                | Acquisition and supply of information products and services | [ISO catalogue](https://www.iso.org/standard/91114.html)                         |
| ISO/IEC/IEEE 26513 | 2017                | Review and testing of information for users                 | [ISO catalogue](https://www.iso.org/standard/67417.html)                         |
| ISO/IEC/IEEE 26514 | 2022                | Design and development of information for users             | [ISO catalogue](https://www.iso.org/standard/77451.html)                         |
| ISO/IEC/IEEE 26515 | 2018                | Information development in agile projects                   | [ISO catalogue](https://www.iso.org/standard/70880.html)                         |

The ISO catalogue lists a replacement for 26513 as [under publication](https://www.iso.org/standard/89070.html).
Recheck that status before the next documentation release.
The 2026 edition of 26512 replaces the 2018 edition.

## Conformance boundary

The user authorized public sources for this revision.
The ISO catalogue abstracts establish subjects and editions.
They do not provide every normative requirement.
The indexed ASD source provides writing rules, but direct retrieval of the complete official PDF returned HTTP 403 during preparation.

This revision applies the project [writing rules](WritingRules.md) and [information plan](../Maintenance/InformationPlan.md).
It does not claim complete ASD-STE100 or ISO/IEC/IEEE 2651x conformance.
Full conformance remains unverified until the complete applicable requirements and the language dictionary receive an evidence-based review.
Short sentences and a common page structure alone cannot establish conformance.

The [evidence matrix](Conformance.md) records the implemented controls and the remaining evidence gaps.
It is a project mapping, not a reproduction of the standards.
Do not invent clause numbers from public summaries.

## Release rule

1. Record the documentation revision.
2. Record the product revision that the documentation describes.
3. Complete the [documentation review](../Maintenance/Review.md).
4. Record each unresolved requirement in the evidence matrix.
5. Publish the verified scope with the document set.

If a requirement has no evidence, report it as unverified.
Do not replace that status with a conformance badge or an unsupported approval statement.

## Related information

- [Technical terms](Terminology.md)
- [Documentation delivery](../Maintenance/Delivery.md)
- [Documentation publishing](../Publishing.md)
