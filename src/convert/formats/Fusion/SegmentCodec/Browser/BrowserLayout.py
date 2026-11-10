# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

# the observed browser root record starts with this exact native identifier
KRootLabel = "PersistBrowserRootId"

# the alternate route flag occurs in an older capture and remains a distinct key
KRouteFlags = frozenset((0, 1))

# bounded route lists prevent untrusted counts from determining decoder work
KMaxRoutes = 128

# both native group orders contain one singleton and one five folder list
KFolderSizes = (1, 5)

# the native role names are narrow strings and have a bounded field size
KMaxLabelLength = 128

# the whole root limit bounds even malformed inputs before parsing nested counts
KMaxRootLength = 8192
