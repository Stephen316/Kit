<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Generator formatter dependency

The dev extra might appear complete for pytest. The generation check starts a subprocess that imports Black. Include the pinned formatter in that extra when separating scanner dependencies. See [the finding](https://github.com/TryUniCAD/Kit/pull/72#discussion_r4546730884).
