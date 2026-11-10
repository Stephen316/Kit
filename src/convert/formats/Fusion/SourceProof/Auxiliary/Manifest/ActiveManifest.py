# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

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
