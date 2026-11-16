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
- [Definition journal](../../../../re/solidworks/WriterResearch/DefinitionJournal.md) uses the installed loader and the same 25 archives to establish the attachment, default notebook and saved appearance identifier counter. An isolated encoder reproduces the observed 81-byte notebook span and accepts two independently supplied typed attachments. The [Definition tail codec](SolidWorksDefinitionTail.md) accounts for the four additional generation-19000 bytes as an empty variability count before the part's terminal double. Earlier outer Definition fields still need attribution.
- [Empty material manager](SolidWorksMaterialManager.md) emits the unsigned appearance counter and empty object list. Its reader returns the offset of the document's next string.
- [Definition options fragment](SolidWorksDefinitionOptions.md) composes the journal, notebook, material manager and typed document defaults through the end of the rendering-options block.
- [Definition fragment assembly](SolidWorksDefinitionFragment.md) continues from the rendering options through the remaining document fields, empty variability count and terminal part double.
- [Complete Definition stream](SolidWorksDefinitionStream.md) combines the typed modern prefix and journal-to-end fragment with explicit user, view and camera inputs.
- [Blind depth](../../../../re/solidworks/WriterResearch/BlindDepth.md) encodes the named `moLengthParameter_c` fragment from a requested depth and allocated class references. Two independently supplied depths decode through the existing typed reader. The enclosing display record still has unresolved fields.
- [Blind boss display style](SolidWorksBossDisplayStyle.md) constructs the 94-byte appearance span from the inherited display-item serializer and constructor defaults verified across all eight P03 controls.

The corpus pass checked native file sizes and hashes against the committed receipts. The work includes no production writer registration. Complete configuration and resolved-archive construction, qualified portable inputs, and an application-verified generated part remain open. The [step register](../../../Reference/Research/AutomationSteps.md#a12-solidworks-writer-research) tracks the qualification dependencies.
