# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# metadata follows the same member limit as the native fusion archive reader
KMaxMetaSize = 64 * 1024 * 1024

# registry counts match the index reader before any record instances are allocated
KMaxMetaClasses = 100000

# both identity tables and stored lists follow the native index count limit
KMaxMetaIds = 1000000

# property counts stay within the versioned index reader bound
KMaxMetaProps = 1024

# counted text uses the native cursor limit in narrow and wide fields
KMaxMetaText = 4096
