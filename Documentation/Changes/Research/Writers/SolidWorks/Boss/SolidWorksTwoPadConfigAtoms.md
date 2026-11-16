<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Construct the merged two-pad Config-0 atom manager

The [five sealed SOLIDWORKS saves](../../SolidWorksTwoPadDiscovery.md) retain two configured atoms and one joined solid. The allocation counter is 102. The archive files upper atom 102 first as the schema-1 `moAtom_c` definition at occurrence 58. It files base atom 101 second as a reference to that class at occurrence 59. The saved flags are 0 for the upper atom and 1 for the base atom. Each record retains its own feature ID in both feature references and the same joined solid tag in both geometry references. The typed resolved stream reaches the upper transfer at 58 and the base transfer at 59. The upper operation also reaches 59 as its parent transfer.

The [merged-pad writer](../../../../../../re/solidworks/WriterResearch/TwoPadAtoms/WritePadAtoms.py) takes both feature IDs and the joined kernel tag explicitly. It uses the existing guarded atom-body encoder and the current archive allocator. The emitter allocates occurrences in saving order, preserves the preallocated atom identities, and ends at the generation return before the ghost manager. In the discovery saves the resulting span is 206 bytes. The existing relation reader independently reaches the same next archive slot and the relation manager beyond the ghost record.

The [offline verifier](../../../../../../re/solidworks/WriterResearch/TwoPadAtoms/VerifyPadAtoms.py) reproduces all five spans byte for byte from the typed ownership and recorded body tags. The two independently authored baselines share span SHA-256 `55925e6fbd3bda4cd49dd6f438770e9048709d0b26d49d876213b9a18ec71170`. A fresh map with feature IDs 73 and 118 and solid tag 41023 produces `3457f1850adf03beadb8986ffe689ff1e9bb373d92851d16b28b1e299f15cbb9`. Eleven invalid ownership and modified record controls fail. The original P01/P03 zero- and one-atom replay over fourteen saves retains SHA-256 `193129f1559b395334b21a75f00b49ccf19f343b83ccb95ce63bdab175d83865`. [Original atom fields and native serializer references](../../../../../../re/solidworks/WriterResearch/ConfigAtomManager.md)

The 1,708-byte verifier result is `210b784f22310e522531473ca1eb4acb91e0ee117c1e04aa320c7e687120da94`. Run the verifier with the source revision and the report, authoring and reopen SHA-256 values from the sealed discovery audit.

This work reproduces one configured span. Full two-pad generation still requires the kernel and rollback producer, the face-supported upper profile and resolved merge, and a fresh licensed open, rebuild, edit, save, and reopen of a generated part.
