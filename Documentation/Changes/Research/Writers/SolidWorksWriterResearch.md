<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS writer research for a rectangular blind boss

The A12 research targets an origin-anchored rectangle and one forward blind additive extrusion in SOLIDWORKS generation 19000. The [portable mapping and refusal matrix](../../../../re/solidworks/WriterResearch/PortableBoss.md) trace the profile, support, constraints, and driving parameters through the saved archives and describe the initial writer boundary.

- [Configuration atoms](../../../../re/solidworks/WriterResearch/ConfigAtoms.md) verifies 30 typed feature-to-atom joins across 25 discovery documents. Three P04 controls save their atoms in an order that differs from the feature history, so the writer needs symbolic transfer ownership.
- [Model header](../../../../re/solidworks/WriterResearch/ModelHeader.md) derives the self item’s class allocation from actual history lengths and checks the geometric frame against 25 controls. Fourteen edit or inch controls expose the existing ordinal assumption in the header reader.
- [Definition journal](../../../../re/solidworks/WriterResearch/DefinitionJournal.md) uses the installed loader and the same 25 archives to establish the boundary of the `uoJournal_c` attachment inside its notebook. An isolated encoder reproduces the observed attachment bytes and accepts two independently supplied typed records. The complete notebook's additional four bytes in generation 19000 still need a field rule.
- [Blind depth](../../../../re/solidworks/WriterResearch/BlindDepth.md) encodes the named `moLengthParameter_c` fragment from a requested depth and allocated class references. Two independently supplied depths decode through the existing typed reader. The enclosing display record still has unresolved fields.

The corpus pass checked native file sizes and hashes against the committed receipts. The work includes no production writer registration. Complete configuration and resolved-archive construction, qualified portable inputs, and an application-verified generated part remain open. The [step register](../../../Reference/Research/AutomationSteps.md#a12-solidworks-writer-research) tracks the qualification dependencies.
