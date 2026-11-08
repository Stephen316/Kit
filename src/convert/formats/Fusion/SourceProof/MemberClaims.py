# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from re import compile as CompilePattern

from convert.formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive
from convert.formats.Fusion.SourceProof.LedgerInput import KDesignStreams
from convert.formats.Fusion.SourceProof.ProofClaim import (
    ProofCategory,
    ProofClaim,
    ProofScope,
)

# native configuration table and rule identities use the canonical five part uuid layout
KConfigUuid = r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}"

# the observed active configuration names address the two separately stored json roles
KConfigMember = CompilePattern(
    r"FusionAssetName\[Active\]/DesignConfigurationTable\.BlobParts/"
    rf"(?:DesignConfigurationTable\.{KConfigUuid}\.dsgcfg|"
    rf"DesignConfigurationRule\.{KConfigUuid}\.dsgcfgrule)"
)


# proof reads can settle empty configuration content while leaving opaque attachments visible
def ReadMemberClaims(
    Archive: IndexedArchive, Scope: ProofScope
) -> tuple[ProofClaim, ...]:
    Loaded = Archive.ReadNames
    Claims = []
    for Member in Archive.Members:
        if Member.Name in KDesignStreams:
            Claims.append(
                ProofClaim(
                    Scope, Member, ProofCategory.KStructural, "active design index"
                )
            )
        elif Member.Name in Loaded:
            Claims.append(
                ProofClaim(
                    Scope,
                    Member,
                    ProofCategory.KObserved,
                    "referenced native cache read",
                )
            )
        elif Member.Size == 2 and KConfigMember.fullmatch(Member.Name):
            try:
                Content = Archive.ReadMember(Member.Name, 2)
            except ValueError:
                continue
            if Content == b"{}":
                Claims.append(
                    ProofClaim(
                        Scope,
                        Member,
                        ProofCategory.KVerifiedAuxiliary,
                        "empty configuration object",
                    )
                )
    return tuple(Claims)
