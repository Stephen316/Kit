<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Public SOLIDWORKS and Fusion route preflight

The A13 preflight ran the public `open_document` and `write_document` APIs on the paired P01 and P03 baseline discovery archives at source `5093d70006f9687a3ddd81ede82ced50c85ebb1b`. It tried each direction with strict and partial reads and disabled writer carriers. All eight attempts preserved the source bytes and left the temporary destination absent. The retained receipt SHA-256 is `03c3be3acb91c8cbe8cab187ece875db17863d897e79f864141d76312e2481e6`. [Pinned paired archive comparison](RectangularPairEvidence.md)

| Direction            | Case                         | First observed boundary                                                                                                                                      |
| -------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| SOLIDWORKS to Fusion | P01 and P03, both read modes | The source sketch carried a typed saved principal support and the write admission gate refused it. The P01 document had zero neutral bodies and P03 had one. |
| Fusion to SOLIDWORKS | P01 strict                   | The strict reader required an extrusion following the sketch.                                                                                                |
| Fusion to SOLIDWORKS | P03 strict                   | The strict reader encountered an unmodeled native semantic entity class.                                                                                     |
| Fusion to SOLIDWORKS | P01 and P03 partial          | The reader returned a document with a partial-history diagnostic. Writer lookup found no SLDPRT writer.                                                      |

A separate offline diagnosis at source `916572946debd94ae0d52f59c7f8140a8ef0bafe` observed four exact P01 and P03 XY and YZ archives in both read modes. Each saved sketch support pointer named its selected principal datum. Its four-byte span lay inside the corresponding sketch record, and the datum's frame span came from the same resolved feature stream. Private process instrumentation observed the next existing guard in isolation. It refused 25 native-only feature definitions in each case, including the native presentation rows and sketch feature. All eight destinations stayed absent and the source hashes matched. The retained diagnostic receipt SHA-256 is `3500869c933ea623794dfb42c97acdc65aebec8d22376b7adf40a6db5a6ca5e5`. [Saved support evidence](../SolidWorksPublicSketchSupport.md), [native-semantic write policy](../NativeSemanticWriteQualification.md)

The production guards still apply, and the Fusion production writer requires its own typed authoring or native-state contract. A13 needs independently verified writer output in both licensed target applications, including healthy controls, body and history measurements, and driving parameter edits followed by restoration, rebuild and reopen. The current route receipts establish offline refusal boundaries. [A13 exit criteria](../../../../Reference/Research/AutomationSteps.md)
