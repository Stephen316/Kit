# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

# the fusion index limits the amount of central directory state
KMaxZipEntries = 4096

# a portable member name stays below common filesystem path limits
KMaxZipName = 4096

# individually encoded paths should fit common filesystem component limits
KMaxPathPart = 255

# bounded nesting keeps portable path conflict checks cheap
KMaxPathDepth = 64

# both stored and expanded member lengths must fit the archive index limit
KMaxMemberBytes = 64 * 1024 * 1024

# generated archives fit both the input and declared expansion limits
KMaxArchiveSize = 128 * 1024 * 1024

# generated central data stays within the public probe limit
KMaxCentralSize = 4 * 1024 * 1024
