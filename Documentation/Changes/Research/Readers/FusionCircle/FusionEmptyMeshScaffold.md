<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Read vendor-saved circles with an empty Fusion mesh scaffold

The strict reader recognizes the original `ParaMeshBodies` and
`ParaMeshTextureStore` classes from the typed native catalog. It verifies
one empty scaffold owned by the projected component, a single texture
store linked from that scaffold, empty texture maps, and the witnessed
default creation and display state. Existing mesh payload and unsupported
semantic state checks still apply.

Two independently reopened [vendor-saved circle archives](../../../../../re/Fusion/LocalOracle/RotationalDocuments/NativeAcceptance.json)
exercise the strict read. The native measurements record one closed
profile, one circle centered on the sketch origin, and a 16 mm radius.
The strict public reader projects the same circle and loop. An archive
with a nondefault scaffold state must still fail the same public read
boundary. [Process boundary coverage](../../../../../tests/Convert/Api/Fusion/Native/VendorCircleTests.py)

The locked local replay reproduced both circle reads and refused a scaffold
whose visibility differed from the saved default. The replay also checked the
SHA-256 and MetaStream class registrations of all 563 pinned F3D archives in the
[reader census](../../../../../re/automation/FusionOutcomes.json) with the prior
strict refusal `Unknown native Fusion entity class`. None registered either
scaffold GUID.

The archive evidence covers the measured standalone sketch and its
empty scaffolding. The historical radius and diameter dimension class
refusals retain their own acceptance requirements.
