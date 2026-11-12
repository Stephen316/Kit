# Fusion research import and explicit reader

## Change

The import adds the Fusion study under `re/Fusion/Study`.
Feature notes and reproduction guidance reside under `re/Fusion/Notes`.
Historical research files retain their bytes and provenance.
The research exemption does not establish production acceptance.

The same change adds SDK parsing and projection modules, shared feature models, and FreeCAD feature writing and edit reconciliation.
It also includes corresponding integration coverage.
The change is larger than a research-corpus import.

## Availability

Production discovery excludes `Fusion`.
It must not advertise or resolve `fusion.f3d` or the `f3d` alias.
Research callers instantiate `FusionReader` explicitly with `ReadOptions`.
See [the research reader guide](../../re/Fusion/Notes/SdkReader.md).
Tests opt in through `tests/convert/FusionRead.py`.
That opt-in is not a production registration mechanism.

## Limits

The reader projects qualified history, parameters, sketches, bodies, and assembly data.
History selection, feature coverage, and compression variants have documented limits.
FreeCAD writing and readback cover selected feature families.
The change does not establish full parametric translation or complete native Fusion writing.
It also does not establish target-application acceptance for arbitrary input.

## Recorded verification

The compliance repair used Black, Prettier, and whitespace checks.
It extracted catalogue alias assertions and shortened a rationale-policy integration test name.
The assertions remain in place.
No local tests ran during that repair.
Earlier study audits remain historical evidence.
Remote CI, current-head review, and merge-group acceptance require their own results.

See [the feature index](../../re/Fusion/README.md), [saved-file workflow](../../re/Fusion/Notes/Workflow.md), and [queue guide](../../MergeQueue.md).
