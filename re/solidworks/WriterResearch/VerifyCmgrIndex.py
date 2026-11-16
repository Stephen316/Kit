from hashlib import sha256
from struct import unpack

from CmgrIndex import KConfigurationIndex, CmgrIndex, EncodeCmgrIndex, ReadCmgrIndex
from CmgrOpening import ReadOpenFields
from HeaderLogs import ReadHeaderLogs
from HeaderSelf import ReadHeaderSelf
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import SldprtArchive


def verify_cmgr_index(Archive: SldprtArchive, Generation: int) -> str:
    _, Opening, Slots = ReadOpenFields(Archive.require("Contents/CMgr"), Generation)
    Saved = Archive.require(KConfigurationIndex)
    Fields = ReadCmgrIndex(Saved, Generation)

    ConfigStream = f"Contents/Config-{Slots.ConfigId}"
    RequireArch(
        all(
            bool(Archive.require(ConfigStream + Suffix))
            for Suffix in ("", "-ModelHeader", "-ResolvedFeatures")
        ),
        True,
        "CMgr index dispatch to the active configuration streams",
    )
    HeaderData = Archive.require(ConfigStream + "-ModelHeader")
    RequireArch(
        HeaderData == Archive.require("Header2"), True, "indexed ModelHeader copy"
    )
    HeaderCursor, Header = ReadHeaderLogs(HeaderData, Generation)
    SharedFile = ReadHeaderSelf(HeaderCursor, Generation)
    _, SessionStamp, _ = unpack("<3I", Archive.require("ModelStamps"))
    RequireArch(
        (Header.UpdateStamp, SharedFile.File.ConfigName),
        (SessionStamp, Opening.NameValue),
        "CMgr index session and active configuration owners",
    )
    Input = CmgrIndex(
        Slots.ConfigId,
        Opening.NameValue,
        Header.UpdateStamp,
        Fields.GeometryStamp,
        SharedFile.ModifiedTime,
    )
    RequireArch(Fields, Input, "CMgr active index matches document state")
    RequireArch(
        EncodeCmgrIndex(Generation, Input) == Saved,
        True,
        "exact standalone CMgr configuration index",
    )
    return sha256(Saved).hexdigest()
