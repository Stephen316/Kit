<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS radial boss discovery readback

The [research command](../../../../../re/automation/SolidWorksRadialEvidence.py) verifies the private three-part SOLIDWORKS discovery capture against its independently recorded attempt digest. It checks the exact source and phase hashes, saved file rosters, controls and distinct owned application processes. It opens the saved archives offline through the existing SDK cursor.

```shell
python re/automation/SolidWorksRadialEvidence.py /private/discovery-capture \
  --receipt-sha256 057b15e1cd8765d2e84086459e1c45f5e397e399791e69e0b190ddd1c7be243f
```

The [archive reader](../../../../../re/automation/SolidWorksRadialArchive.py) follows the typed configuration, resolved prefix and owning sketch. It reads the three point records, resolves the local arc and its seam and center, and binds the G1 value and owned length parameter to that arc. Its second G1 handle has the invalid placeholder state. The active G2 relation joins the circle center to the local proxy of the typed document Origin. The common radial display prefix also verifies. The report preserves the saved spans and identifies the unresolved radial display owner and value slot, circular region and profile return, and complete resolved boss graph.

## Verification

The private licensed run used SOLIDWORKS 2026 build 34.4.1.1011. Three independently authored Front-plane circles with diameters 13, 19 and 23 mm drive 7 mm forward blind bosses. Each source saved, closed, reopened read-only in a separate owned process and rebuilt. Both processes passed their before and after controls. The independent native observations agree with the offline circular radius, diameter ownership and center-to-Origin relation for all three cases. The readback records each exact source and resolved-stream hash.

The local command accepted all three sealed archives and refused both an incorrect attempt digest and a rehashed scratch archive whose owned diameter differed from the parsed circle. The native sources and receipts remained unchanged.

This evidence covers the observed diameter-driven full circular sketch prefix in those three discovery archives. The native capture and archive observations remain separate from portable reader qualification and target application acceptance.

## Circular profile return

On the same sealed cohort, `--profile-return` continues the typed offline readback. The `moSkDimHandleRadial_c` owner resolves to the active sketch and selects its sole G1 diameter value. The two saved display value caches agree with the owned diameter in each archive. The radial subtype return reaches a single sketch region whose outline uses the existing circular entity.

The single profile chain and right trim edge both identify the same native circle. The support reference agrees with the typed Origin datum and the independently observed licensed Front Plane. The saved profile returns at a typed schema-1 `moExtrusion_c` record. The report leaves the complete resolved boss graph unresolved. This check applies to the three positive blind-boss discovery captures on the measured build.

Separate rehashed scratch copies with an incorrect radial value slot or an altered region return were both refused by this mode. The default prefix mode reproduced the original observation, and the sealed inputs remained unchanged.
