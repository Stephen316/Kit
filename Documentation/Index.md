<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Kit documentation

The [Fusion research import](Changes/FusionResearchImport.md) records the explicit
reader boundary, SDK changes, supported research scope, and acceptance limits.

Start with [Getting started](GettingStarted.md), [API reference](Reference/Overview/ApiReference.md), and [architecture](Reference/Architecture/Overview.md).

- [GitHub wiki](https://github.com/TryUniCAD/Kit/wiki)
- [Documentation maintenance and publishing](Publishing.md)
- [GitHub releases and PyPI publishing](Changes/CommitReleases.md)
- [Change entries](Changes/Index.md)
- [Mandatory gotchas log](Gotchas/README.md)

These reference pages began with a generated wiki snapshot and were curated against `aeff047c355622e812ab5d79b665d8f64c4075bb`. The [provenance record](Reference/Provenance.json) preserves original page paths. Maintained docs live in `Documentation/`; future generated sync PRs must be reviewed and normalized before import.

The pages describe implementation and research, not blanket format support or acceptance results. Carrier preservation, native replay, and successful API calls do not establish lossless editable output. Research donor experiments are not production-writing guidance. Follow the [acceptance standard](../.agents/skills/standard-pr-practice/references/Standards/Portable/LosslessTranslation.md).

## Reference

- [Introduction to Kit SDK](Reference/Overview/Introduction.md)
- [API reference](Reference/Overview/ApiReference.md)
- [Contribution workflow](Reference/Overview/Contributing.md)
- [Architecture Overview](Reference/Architecture/Overview.md)
- [Conversion Engine](Reference/Architecture/Engine.md)
- [Neutral Document Model](Reference/Model/Document.md)
- [Assembly & Constraints Model](Reference/Model/Assembly.md)
- [Parametric Features Model](Reference/Model/Features.md)
- [Boundary Representation (B-Rep)](Reference/Model/Brep.md)
- [SOLIDWORKS Format Adapter](Reference/Adapters/Solidworks.md)
- [SOLIDWORKS Feature Resolution](Reference/Adapters/SolidworksFeatures.md)
- [FreeCAD Format Adapter](Reference/Adapters/Freecad.md)
- [CATIA Format Adapter](Reference/Adapters/Catia.md)
- [JSON & Registry Adapter](Reference/Adapters/Json.md)
- [Geometry Translation (Parasolid & OpenCASCADE)](Reference/Data/Geometry.md)
- [Wire Serialization & Payloads](Reference/Data/Serialization.md)
- [Reverse Engineering Methodology](Reference/Research/Methodology.md)
- [Reverse Engineering Tooling](Reference/Research/Tooling.md)
- [Oracle Validation & Donor Fixtures](Reference/Research/Oracles.md)
- [Security Boundaries & Validation](Reference/Operations/Security.md)
- [Policy and governance](Reference/Operations/Policy.md)
- [Translation Testing Strategies](Reference/Operations/Testing.md)
