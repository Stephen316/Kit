<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# openswx attribution

`RotateBytes.py` adapts the byte rotation in `libopenswx/src/internal/rol_codec.h`
from [openswx commit 72291dc962bbf267fa40cd57813b273108ebac53](https://github.com/schwitters/openswx/tree/72291dc962bbf267fa40cd57813b273108ebac53).
The container scanner also follows the payload-boundary advancement and cache-cell
recognition in `libopenswx/src/internal/modern_parser.cc`. Kit retains its own
native writer and rejects ambiguous duplicate streams; openswx is a reader and
its first-physical-copy selection is not adopted.

`ReadParaSection.py` also adapts the chained-frame grammar from
`ScanParasolidBlocks` in `libopenswx/src/container.cc` at the same revision.
Kit validates every zlib member, preserves standalone wrappers, and rejects
damaged sections through its existing strict/permissive reader boundary.

The upstream license follows in full.

```text
MIT License

Copyright (c) 2026 openswx contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
