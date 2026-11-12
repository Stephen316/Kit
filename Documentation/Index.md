# Kit documentation

## Start here

This document set describes the Kit revision stored with these pages.
Use the Git commit to identify the exact revision.
The package version alone does not identify every source change.

Start with [getting started](GettingStarted.md).
Read [the standards scope](Standards/Scope.md) for the language and conformance boundary.
Public sources support this revision's standards mapping.
Complete ASD-STE100 and ISO/IEC/IEEE 2651x conformance remains unverified.

## User tasks

| Task                                | Guide                                               |
| ----------------------------------- | --------------------------------------------------- |
| Prepare a Python environment        | [Install Kit](Tasks/Install.md)                     |
| Identify input and output formats   | [Select a reader and writer](Tasks/SelectFormat.md) |
| Convert a source file               | [Convert a document](Tasks/ConvertDocument.md)      |
| Evaluate preservation and usability | [Evaluate a result](Tasks/InspectResult.md)         |
| Inspect a model before writing      | [Read and write a document](Tasks/ReadWrite.md)     |
| Copy available geometry bytes       | [Extract B-rep payloads](Tasks/ExtractGeometry.md)  |
| Diagnose an exception               | [Error recovery](Tasks/Troubleshoot.md)             |

## API and architecture

- [SDK overview](Reference/Overview/Introduction.md)
- [Public API reference](Reference/Overview/ApiReference.md)
- [SDK architecture](Reference/Architecture/Overview.md)
- [Conversion engine and write boundaries](Reference/Architecture/Engine.md)
- [Contribution workflow](Reference/Overview/Contributing.md)

## Model and data

- [Neutral document](Reference/Model/Document.md)
- [Assembly and constraints](Reference/Model/Assembly.md)
- [Parametric features](Reference/Model/Features.md)
- [Boundary representation](Reference/Model/Brep.md)
- [Geometry translation](Reference/Data/Geometry.md)
- [Serialization and payloads](Reference/Data/Serialization.md)

## Format references

- [SOLIDWORKS adapter](Reference/Adapters/Solidworks.md)
- [SOLIDWORKS feature resolution](Reference/Adapters/SolidworksFeatures.md)
- [FreeCAD adapter](Reference/Adapters/Freecad.md)
- [CATIA adapter](Reference/Adapters/Catia.md)
- [JSON adapter and registry](Reference/Adapters/Json.md)

Adapter registration does not prove complete format coverage.
Carrier preservation and source replay do not prove editable output in another format.
Use the result procedure before making a product acceptance claim.

## Operations and research

- [Security boundaries](Reference/Operations/Security.md)
- [Repository policy](Reference/Operations/Policy.md)
- [Translation verification](Reference/Operations/Testing.md)
- [Research method](Reference/Research/Methodology.md)
- [Research tools](Reference/Research/Tooling.md)
- [Oracle evidence and fixtures](Reference/Research/Oracles.md)

## Documentation standards

- [Scope and edition register](Standards/Scope.md)
- [Writing rules](Standards/WritingRules.md)
- [Technical terms](Standards/Terminology.md)
- [Conformance evidence and gaps](Standards/Conformance.md)

## Maintenance

- [Information plan](Maintenance/InformationPlan.md)
- [Documentation review](Maintenance/Review.md)
- [Delivery and correction records](Maintenance/Delivery.md)
- [Documentation feedback](Maintenance/Feedback.md)
- [Publishing and generated imports](Publishing.md)
- [GitHub releases and PyPI publishing](Changes/CommitReleases.md)
- [Change entries](Changes/Index.md)
- [Known gotchas](Gotchas/README.md)

## Provenance and reading surfaces

The reference set began with a generated wiki snapshot.
The generator and hosted wiki are identified in [ReviewBot.json](../.agents/skills/standard-pr-practice/ReviewBot.json).
The [provenance record](Reference/Provenance.json) retains original export paths and hashes.
Those hashes describe the original export, not the current edited text.
The [GitHub wiki](https://github.com/TryUniCAD/Kit/wiki) is a separate publication surface.
A repository documentation change does not establish that the wiki contains that revision.
