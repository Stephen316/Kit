<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Pyright compatibility

Pyright 1.1.414 recognizes the integer result of literal `struct.unpack_from` formats. The Parasolid unsigned 16-bit and 32-bit readers now return an explicit integer instead of applying redundant `isinstance` checks. Their existing bounds checks and `None` result for invalid offsets are preserved. No configuration or caller changes are required.

Python's [format table](https://docs.python.org/3/library/struct.html#format-characters) specifies integer results for `H` and `I`. Explicit conversion also preserves compatibility with analyzers that infer a less precise unpacked type.

The original [remote Pyright job](https://github.com/TryUniCAD/Kit/actions/runs/42888941281/job/130084609266) reported two `reportUnnecessaryIsInstance` errors. Verification of this correction runs in PR CI; no local tests were run. Merge-group acceptance and vendor-application validation are separate and are not established by this compatibility correction.
