<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Target-limit carriers

`allow_carrier=False` might appear to reject every carrier transfer. The registry treats `target_unsupported` differently from implementation and decoding gaps. Inspect each transfer reason when applying acceptance requirements. See [the write policy](../../../src/convert/adapters/base/WritePolicy.py).
