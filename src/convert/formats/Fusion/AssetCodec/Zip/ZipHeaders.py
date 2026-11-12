from io import BytesIO
from struct import pack as PackValue

from convert.formats.Fusion.AssetCodec.Zip.ZipPlanRow import ZipPlanRow

# the native archives use utf encoding even for ascii member names
KZipUtfFlag = 0x0800

# the deterministic timestamp uses the first day in the zip date format
KZipEpoch = 0x0021

# the native outer archive uses the unix creator and version forty six
KZipCreator = (3 << 8) | 46

# native directory attributes mark the path as a directory on both platforms
KDirectoryAttr = (0o40755 << 16) | 0x10

# regular payloads should never be interpreted as links or executable files
KRegularAttr = 0o100644 << 16


# central and local headers must describe the same compressed bytes and crc
def ZipHeadFields(RowValue: ZipPlanRow) -> tuple[int, ...]:
    return (
        10 if RowValue.NameBytes.endswith(b"/") else 20,
        KZipUtfFlag,
        93 if RowValue.UseZstd else 0,
        0,
        KZipEpoch,
        RowValue.Checksum,
        RowValue.PackedSize,
        len(RowValue.Data),
        len(RowValue.NameBytes),
        0,
    )


# the local entry owns exact sizes so no data descriptor is needed
def WriteLocalMut(Output: BytesIO, RowValue: ZipPlanRow) -> None:
    _ = Output.write(PackValue("<I5H3I2H", 0x04034B50, *ZipHeadFields(RowValue)))
    _ = Output.write(RowValue.NameBytes)


# directory order mirrors physical order and points directly at local entries
def WriteCentralMut(Output: BytesIO, RowValue: ZipPlanRow) -> None:
    AttrValue = KDirectoryAttr if RowValue.NameBytes.endswith(b"/") else KRegularAttr
    _ = Output.write(
        PackValue(
            "<I6H3I5H2I",
            0x02014B50,
            KZipCreator,
            *ZipHeadFields(RowValue),
            0,
            0,
            0,
            AttrValue,
            RowValue.Offset,
        )
    )
    _ = Output.write(RowValue.NameBytes)
