<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Fusion fixture compression

Python 3.11 might appear sufficient for every repository fixture. It raises `NotImplementedError` for ZIP members that use Zstandard. The queue suite uses Python 3.14 for this standard-library support. See [the failure](https://github.com/TryUniCAD/Kit/actions/runs/43155805818/job/130975329739).
