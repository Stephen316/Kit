# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.ArchiveRead.ArchiveMember import ArchiveMember
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.ActiveRoute import (
    ActiveRoute,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActTable import ActTable
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ActiveManifest import (
    ActiveManifest,
)


# exact stream identities qualify record offsets without claiming an authenticated revision
@MakeDataClass(frozen=True, slots=True)
class RouteEvidence:
    Manifest: ActiveManifest
    DesignMember: ArchiveMember
    DesignMetaMember: ArchiveMember
    ActMember: ArchiveMember
    ActMetaMember: ArchiveMember
    Table: ActTable
    Routes: tuple[ActiveRoute, ...]
