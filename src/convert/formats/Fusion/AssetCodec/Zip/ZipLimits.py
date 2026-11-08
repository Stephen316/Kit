# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
