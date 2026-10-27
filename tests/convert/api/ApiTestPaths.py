# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from pathlib import Path as FilePath

# one repository anchor prevents split api tests from duplicating path traversal logic
KRootPath = FilePath(__file__).parents[3]

# one solidworks sample covers native replay and cross format carrier behavior
KSamplePath = KRootPath / "examples" / ".SLDPRT" / "example.SLDPRT"

# one catia sample covers tessellation and exact native replay behavior
KCatPartPath = KRootPath / "examples" / ".CATPart" / "Banjo.CATPart"

# one freecad sample covers archive replay through the shared public api
KFcstdPath = (
    KRootPath / "examples" / "Random" / "V8_engine" / "hex bolt gradeb_iso.FCStd"
)
