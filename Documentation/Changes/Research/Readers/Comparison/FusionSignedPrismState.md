<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Fusion generic journal state transport

The Fusion V2 native-state codec recognizes `JournalModel`, `StreamState`,
`DeltaState`, `BulletinBoard`, and `BulletinChange`. Each decoded journal passes
the existing lifecycle materializer before the state decoder returns it. The
snapshot and topology types were already registered.

The replay opens the original P03 `direction-negative` source at
`89c25945f5833ad9c3a1c6c683df510b5702dd54` and verifies archive SHA-256
`4cfc1e792d33d48e4b80f9829a4496cf70c2059378ce1b3cfa716b3a1c9e8aab`.
It checks complete typed document equality after V2 JSON transport and again
after an in-memory archive re-emission and native readback. The transported
journal has two delta states and one bulletin board with 101 changes. The
compact state JSON has 3,205,853 bytes and SHA-256
`9c299b6ce779af171e9d26206af9076a24c5797e13ef8adcaec10be109390938`.

The exact named history and snapshot parts survive re-emission byte for byte.
Their SHA-256 values are
`402dd0ead7a8f2fe6c9f9ef9d23b198c19784689edf4371b4cad5cd19d71874b`
and `bf3696997f4efda464d0635177df6f2611d148878c1b4874a124b691bc3a7663`.
The [signed prism evidence](FusionSignedPrismEvidence.md) documents the
independent saved geometry and native measurement scope.

The V2 boundary rejects an out-of-range active node, a null stream, a duplicated
delta-state identity, and an omitted bulletin-board field. Ordinary strict reading still
accepts the positive baseline and refuses the negative direction and YZ datum
controls at their existing guards. The public Fusion write route emits zero
bytes for marked V2 state, marker-stripped V2 state, downgraded V1 state, and V1
state with its auxiliary records removed. The replay establishes offline state
fidelity for this pinned source. Licensed authoring and reopening remain separate
qualification work.

The hosted archive test pins the report SHA-256
`9f65aaa183fe35889b3a49587ff93bf962b9d0a6dd826610f163299e4fb91a45`.

```sh
uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/automation/FusionSignedPrism/VerifyJournalState.py
```
