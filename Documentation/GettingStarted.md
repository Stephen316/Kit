<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Getting started

Kit requires Python 3.11 or newer. From an isolated checkout, install the locked environment:

```sh
uv sync --frozen --all-groups --all-extras --python 3.11
```

The distribution is named `kit`, but this revision packages the `convert` and `interchange` Python modules. Import the conversion API from `convert`:

```python
from convert import convert as ConvertDoc

Result = ConvertDoc("bracket.SLDPRT", "bracket.FCStd", allow_carrier=False)
```

The destination suffix selects the writer unless `destination_format` is supplied. Existing destinations are protected by default; use `overwrite=True` only when replacement is intended. Inspect `Result.output`, `Result.dropped`, `Result.requirements`, `Result.application_usable`, and `Result.vendor_loadable`.

`strict=True` controls reader validation. `allow_carrier=False` separately rejects outputs whose attestation fails application usability, vendor loadability, no dropped capabilities, or no unmet requirements. The default `allow_carrier=True` can preserve neutral data in a carrier that the target application cannot use. Neither an attestation nor a successful function return replaces target-application acceptance evidence.

See the [API reference](Reference/Overview/ApiReference.md), [conversion engine](Reference/Architecture/Engine.md), and [gotchas](Gotchas/README.md). Dependency installation is not test execution; run tests only in remote CI, as required by [AGENTS.md](../AGENTS.md).
