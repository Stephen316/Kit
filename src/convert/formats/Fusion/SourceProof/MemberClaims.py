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
    + rf"(?:DesignConfigurationTable\.{KConfigUuid}\.dsgcfg|"
    + rf"DesignConfigurationRule\.{KConfigUuid}\.dsgcfgrule)"
)


# proof reads can settle empty configuration content while leaving opaque attachments visible
def ReadItemClaims(
    Archive: IndexedArchive, Scope: ProofScope
) -> tuple[ProofClaim, ...]:
    Loaded = Archive.ReadNames
    Claims: list[ProofClaim] = []
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
