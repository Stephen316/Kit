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

## Source-derived Fusion research candidates

`SourceRectangleProbe.py` derives the two lengths from the pinned SOLIDWORKS neutral drivers and independently measured side bindings. It generates a private Fusion archive for each positive XY P01 case. Offline readback resolves the reciprocal sketch feature and principal XY datum, the four-edge closed perimeter, four edge-axis relations, a distinct Origin and corner, and the two directly bound sketch-owned drivers. Each dimension's actual saved operands match its source side. The three perimeters matched with zero endpoint error for 40 × 20 mm, 41 × 20 mm and 40 × 23 mm.

```sh
python re/Fusion/Reconstruction/DimensionAuthoring/SourceRectangleProbe.py \
  --output /private/P01Candidates
python re/Fusion/Reconstruction/DimensionAuthoring/SourceRectangleProbe.py \
  --prepare-baseline /private/P01Candidates --output /private/P01BaselineWitness
```

The second command rechecks the committed generators, original source receipt, exact target archive and typed bindings. It seals the baseline in the format of the existing two-process witness. The baseline plan retains the source archive and candidate-manifest pins in its copied proof. Run its two phases on separate fresh licensed Fusion processes using the [native witness procedure](../../../Fusion/Authoring/FusionOriginCoincidenceProbe.md#prepare-the-two-process-native-witness), and verify the sealed output with [the existing witness verifier](../../../Fusion/Authoring/FusionWitnessVerification.md).

At `32b452c9f3cc58bd91a4831c6373bc60e5f01b24`, the three-archive candidate report SHA-256 was `3777e33430b8fcbf95915fad6cc49d548f9db15b0e847d68756b9162186b0a5b`. The prepared 57,976-byte baseline archive SHA-256 was `ab974f435ec27ce510e7949a026061e4a7a48111441929eb040882db0e63444f`, and the plan SHA-256 was `d92dc2914966d77bdba348355993c1eab757d89a99ac7c3f1c0553ec8df9ebe0`. The offline witness verifier re-read the sealed plan. Licensed execution of the source-derived baseline and the P03 Boss writer remain open. The separate [fixed Fusion native witnesses](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6921349933) already have licensed edit, restoration and reopen evidence.
