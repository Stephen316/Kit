<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Fresh ordinary part preview rasters

The research renderer draws one closed rectangular sketch on the generated
Front or Right principal datum in generation 19000. A single optional
blind extrusion starts on that sketch and extends by the existing signed
depth. The input corners use sketch-local metres. All four authored lines
must connect the rectangle before the renderer transforms it into world
coordinates through the shared principal frame. With a solid, the renderer
builds the signed opposite cap and draws the three faces visible in the
positive world octant.
[Ordinary profile](OrdinaryProfile.py), [boss state](BossResolve.py),
[principal frames](PrincipalPlaneView.py)

A fixed orthographic view preserves projected proportions and anchors
the viewport to the source sketch over both signed directions. A sketch
has a perimeter with an empty interior. A boss has filled visible faces
and ink on their edges. The caller supplies three RGB colors for the
background, outline, and uniform face fill. These choices describe fresh
presentation and carry no native appearance or material claim.

`RenderPartPreview` returns a top-down 1420 × 710 raster with one index
per pixel and a top-down 640 × 480 raster with four RGBA8 bytes per pixel.
Palette indices 0, 1 and 2 match the caller's color order. The RGBA image
has alpha 255, and the wrapper can encode the index raster with the same
caller colors. The renderer has no archive reads, uses no saved pixels,
and leaves the separately owned image wrappers and package integration
open. [Renderer](PartPreview.py), [wrapper handoff](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6924776824)

## Sealed geometry and raster checks

The verifier reads the generation-19000 archive profile and its optional
boss from each of the six P01 and eight P03 SOLIDWORKS discovery saves
pinned at `466dcb172dfa3803463e07ccde963ba01671d200`. It joins the
rendered outline to the four independently measured world edges. For
each solid it checks the signed depth and compares all vertices of the
three displayed faces against the licensed sketch, support and depth
observations. The verifier checks the drawn ink at every visible face
vertex and the presence or absence of solid fill at the face centers
on both canvases.
[P01 receipt](../../automation/PairedCaptures/P01/solidworks-75b9308cf13e/receipt.json),
[P03 receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json)

```sh
python re/solidworks/WriterResearch/VerifyPartPreview.py
```

The width, height, support, depth and direction controls change the
appropriate raster pairs. Both repeat saves and both inch-display
variants reproduce the corresponding baseline raster. The 14 source
and raster pairs have an aggregate SHA-256 of
`34cf042b07d9022f1121911aa6375d789822dc736b2fd132a104b76f98b8dbc5`.
A different supplied palette changes the RGBA colors while retaining
the geometry indices. Six negative controls refuse an unsupported
datum, a diagonal perimeter, zero or nonfinite depth, an unsupported
generation, and an ambiguous palette. [Verifier](VerifyPartPreview.py)

The replay checks fresh pixels and measured geometry. Encoding and native
acceptance of a substituted preview pair in a generated part require
separate evidence.
