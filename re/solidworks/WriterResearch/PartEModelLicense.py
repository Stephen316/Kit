# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Construct the measured modern standalone part eModel package field."""

from struct import pack as PackFields

from PartFraming import VersionStorage
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

# the member is owned by the native eModel save path
KEModelLicense = "Contents/eModelLic"

# all supported generation part captures measured this explicit package code
KMeasuredPackage = 4


# package metadata comes from the caller owned native save context
def EncodeEModelLicense(Generation: int, PackageCode: int) -> bytes:
    VersionStorage(Generation)
    RequireArch(
        (type(PackageCode), PackageCode),
        (int, KMeasuredPackage),
        "measured eModel licensed package code",
    )
    return PackFields("<I", PackageCode)
