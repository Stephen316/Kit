# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.ArchiveRead.IndexedArchive import (
    IndexedArchive,
    KDesignPrefix,
)
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ActiveManifest import (
    ActiveManifest,
)
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadAssetMeta import (
    ReadAssetMeta,
)
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadRootMeta import (
    ReadRootMeta,
)

# root document metadata resides outside every asset directory
KRootManifest = "Manifest.dat"

# only the active asset manifest can authorize its change table association
KActiveManifest = (
    KDesignPrefix.removesuffix("FusionDesignSegmentType1/") + KRootManifest
)

# both observed manifests are small and user text has a finite native bound
KMaxManifestBytes = 32 * 1024


# exact member and asset identity joins exclude foreign archive metadata
def ReadActiveManifest(Archive: IndexedArchive) -> ActiveManifest:
    Members = {Member.Name: Member for Member in Archive.Members}
    RootMember = Members.get(KRootManifest)
    ActiveMember = Members.get(KActiveManifest)
    if (
        RootMember is None
        or ActiveMember is None
        or any(
            Member.IsDirectory or not 0 < Member.Size <= KMaxManifestBytes
            for Member in (RootMember, ActiveMember)
        )
    ):
        raise ValueError("Missing or oversized Fusion manifest member")
    RootId, RootVersions = ReadRootMeta(
        Archive.ReadMember(RootMember.Name, KMaxManifestBytes)
    )
    AssetId, SnapshotId, AssetVersions = ReadAssetMeta(
        Archive.ReadMember(ActiveMember.Name, KMaxManifestBytes)
    )
    if RootId != AssetId:
        raise ValueError("Fusion root and active manifest asset IDs disagree")
    return ActiveManifest(
        RootMember, ActiveMember, AssetId, SnapshotId, RootVersions, AssetVersions
    )
