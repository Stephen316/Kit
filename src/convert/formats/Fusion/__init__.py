# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

"""Native Fusion format parsing."""

from convert.formats.Fusion.DocumentRead import ReadFusionDoc

# explicit exports keep the partial inspection entry point discoverable
__all__ = ("ReadFusionDoc",)
