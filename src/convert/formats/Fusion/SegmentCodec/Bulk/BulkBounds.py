# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

# the metadata registry starts assigning file local class codes here
KMinClassCode = 256

# a bulk class code must fit the largest supported metadata class table
KMaxClassCode = KMinClassCode + 100_000 - 1

# native record identities occupy an unsigned word of eight bytes
KMaxWireId = (1 << 64) - 1

# generated streams must fit the native archive member reader limit
KMaxBulkBytes = 64 * 1024 * 1024

# the metadata reader caps its primary and continuation lists independently
KMaxIndexRows = 1_000_000
