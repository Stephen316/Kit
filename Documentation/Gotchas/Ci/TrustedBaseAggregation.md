<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Trusted-base aggregation

A reporter change on a PR might appear to affect that PR's aggregate. `pull_request_target` loads trusted base code. Merge the reviewed reporter change before relying on its behavior elsewhere. See [the CI allowlist](../../Changes/CiReviewerExclusions.md).
