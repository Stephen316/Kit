# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.ArchiveRead.ArchiveMember import ArchiveMember


# the receipt retains both member identities with the fields used for active routing
@MakeDataClass(frozen=True, slots=True)
class ActiveManifest:
    RootMember: ArchiveMember
    ActiveMember: ArchiveMember
    AssetId: str
    SnapshotId: str
    RootVersions: tuple[tuple[str, int], ...]
    AssetVersions: tuple[tuple[str, int], ...]
