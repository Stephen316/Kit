from zlib import crc32 as CrcValue

from convert.formats.Fusion.ArchiveRead.ArchiveMember import ArchiveMember
from convert.formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive
from convert.formats.Fusion.ArchiveRead.ReadDesignPair import KDesignPrefix
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SourceProof.Auxiliary.ReadAuxFrame import (
    AuxFrame,
    KActivePrefix,
)


# supplied frame bytes must agree with the exact same archive member facts
def ReadRouteFiles(
    Archive: IndexedArchive, DesignBulk: bytes, DesignMeta: bytes, ActFrame: AuxFrame
) -> tuple[ArchiveMember, ArchiveMember]:
    Members = {Member.Name: Member for Member in Archive.Members}
    ActPrefix = f"{KActivePrefix}{SegmentKind.KAct.value}1/"
    DesignMember = Members.get(KDesignPrefix + "BulkStream.dat")
    DesignIndex = Members.get(KDesignPrefix + "MetaStream.dat")
    if (
        DesignMember is None
        or DesignIndex is None
        or Members.get(ActPrefix + "BulkStream.dat") != ActFrame.BulkMember
        or Members.get(ActPrefix + "MetaStream.dat") != ActFrame.MetaMember
    ):
        raise ValueError("Fusion ACT route members disagree with archive")
    for Member, Content in (
        (DesignMember, DesignBulk),
        (DesignIndex, DesignMeta),
        (ActFrame.BulkMember, ActFrame.BulkData),
    ):
        if (
            Member.IsDirectory
            or Member.Size != len(Content)
            or Member.Crc != CrcValue(Content)
        ):
            raise ValueError("Fusion ACT route member content disagrees with archive")
    return DesignMember, DesignIndex
