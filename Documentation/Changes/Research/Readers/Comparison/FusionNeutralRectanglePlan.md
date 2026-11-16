<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Neutral rectangle mapping against the Fusion constructor

This A13 preflight reads seven SOLIDWORKS discovery archives at capture revision `89c25945f5833ad9c3a1c6c683df510b5702dd54`. It pins each archive and its observation from the separately reopened SOLIDWORKS capture. It compares the verified source fields with an in-memory `MakeFusionDoc` graph. The mapping remains unqualified. Public writer admission still refuses these source documents. [Public route refusal](RectangleRoutePreflight.md), [historical rectangle evidence](RectangularPairEvidence.md)

The report derives width and height from each named source parameter and its owned, ordered size operands on the measured perimeter sides. It derives the P03 depth from the saved Boss profile reference, direction and typed depth binding. Per-binding output retains the source relation and parameter IDs, operands in world millimeters, and source byte spans. It records the constructor's relation, model parameter and dependent user parameter.

| Source cases                 | Bound values in millimeters                            | In-memory comparison                                                                                            |
| ---------------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| P01 baseline and two edits   | 40 × 20, 41 × 20, 40 × 23                              | Matching perimeter, axis targets and dimensions                                                                 |
| P03 baseline and three edits | 40 × 20 × 10, 41 × 20 × 10, 40 × 23 × 10, 40 × 20 × 12 | Matching perimeter, axis targets and dimensions. Constructor prism volumes of 8,000, 8,200, 9,200 and 9,600 mm³ |

The SOLIDWORKS source has a separate origin coincidence and two directly owned sketch drivers. The Fusion constructor fixes a corner and uses global width and height parameters linked to two model dimensions. It adds a length parameter to P01. For P03 the report preserves the initial SOLIDWORKS Join and the constructor's Create, along with its explicit along-distance link and taper model parameter. Each source still carries 25 native-only feature definitions at the transfer boundary. [Public Fusion authoring contract](../../../Fusion/Adapter/FusionPublicAdapter.md)

The existing origin and sketch-owned probes compose for the fixed Owned witness. The composed research generator explicitly overwrites the sketch name, dimensions and driver names. Its checked native dimension operands follow the existing probe's order, and its proof applies to a sketch-only archive. Source-driven use needs an authoring contract that accepts the verified source bindings and corroborates the stored profile and feature semantics. The preflight keeps the two licensed witnesses as separate evidence and emits no native archive. [Origin probe](../../../Fusion/Authoring/FusionOriginCoincidenceProbe.md), [sketch-owned probe](../../../Fusion/Authoring/FusionOwnedDimensionProbe.md)

Run the report from the repository with Python 3.14. The canonical JSON SHA-256 is `06ad424e2ce4d40da9211163a55a8f5dbe8751cd25594120e71fd1a433028d58`. [Replay](../../../../../re/automation/FusionNeutralRectanglePlan.py), [archive gate](../../../../../tests/Research/Archives/ArchiveEvidenceTests.py)

```sh
uv run --frozen --python 3.14 python re/automation/FusionNeutralRectanglePlan.py
```
