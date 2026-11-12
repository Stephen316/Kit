<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Geometry translation and payloads

## Purpose

Kit translates implemented geometry representations through the neutral B-rep model.
This page distinguishes geometry decoding, payload extraction, and parametric acceptance.

## Representations

| Format                  | Common container          | Kit information                                        |
| ----------------------- | ------------------------- | ------------------------------------------------------ |
| Parasolid transmit data | SOLIDWORKS streams        | Payload bytes and implemented neutral B-rep structures |
| OpenCASCADE ASCII B-rep | FreeCAD archive members   | Curves, surfaces, and topology                         |
| Tessellation            | Format-specific resources | Display meshes                                         |

A payload can exist without complete neutral decoding.
A neutral geometry model can exist without an editable feature history.
Keep those states separate in reports.

## Parasolid path

The source reader locates geometry in the implemented SOLIDWORKS container records.
The partition stream is one important source of cached body data.
The geometry code handles its supported framing and transmit records.
Unsupported grammar must remain an explicit limitation.

Do not infer a universal Parasolid decoder from one successful payload extraction.
Do not infer a vendor-loadable target from a successful encoder return.

## OpenCASCADE path

The FreeCAD geometry path uses ASCII B-rep data and related archive members.
The format includes the literal header `CASCADE Topology V1, (c) Matra-Datavision` in the documented representation.
A matching header identifies a format candidate.
It does not validate the complete shape.

The archive can also contain element maps that relate geometry to native object names.
Preserve those relationships when the target workflow depends on selections.

## Cache behavior

Feature history and geometry caches have different roles.
Some vendor versions can regenerate particular caches from valid authored records.
That behavior requires evidence for the exact feature family and build.

Do not omit a cache solely because another sample rebuilt successfully.
Do not write plausible geometry values without a derivation.
Incorrect caches can cause failed loads, empty bodies, or incorrect geometry.

## Units and identity

Keep units explicit when comparing geometry.
Record transforms and body identifiers with the payload.
A matching volume does not establish matching center of mass or orientation.
A matching body count does not establish matching topology.

## Extract or translate

Use [B-rep extraction](../../Tasks/ExtractGeometry.md) to copy available payload files.
Use [conversion](../../Tasks/ConvertDocument.md) to request a target document.
Use [result evaluation](../../Tasks/InspectResult.md) to evaluate the output.
These tasks have different success conditions.

## Sources

- [Parasolid geometry](../../../src/convert/geometry/Parasolid.py)
- [OpenCASCADE geometry](../../../src/convert/geometry/Opencascade.py)
- [FreeCAD B-rep handling](../../../src/convert/adapters/freecad/Brep.py)
- [Neutral B-rep model](../Model/Brep.md)
