from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgCryptHeader import (
    DwgCryptHeader,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader

# author version must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KAuthorVersion = "AC1032"

# max page size needs one explicit bound so native drawing authoring cannot accept inconsistent resource or layout limits
KMaxPageSize = 0x7400

# file header must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KFileHeader = DwgFileHeader(
    KAuthorVersion,
    bytes(5),
    0,
    3,
    0,
    33,
    0,
    30,
    bytes(3),
    0,
    0,
    0,
    0,
    0x80,
    0,
    0,
    (1027, 335, 285, 285) + (0,) * 15,
)

# crypt header must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KCryptHeader = DwgCryptHeader(
    "AcFssFcAJMB",
    (0, 108, 4),
    0,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    0,
    (32, 128, 64),
    0,
    0,
    0,
    0,
    0,
    0,
    True,
)

# the section rows order must stay explicit so drawing objects retain valid ownership and reference relationships
KSectionRows = (
    ("AcDb:AppInfo", 10, 768, 1),
    ("AcDb:SummaryInfo", 9, 128, 1),
    ("AcDb:RevHistory", 8, KMaxPageSize, 2),
    ("AcDb:AcDbObjects", 7, KMaxPageSize, 2),
    ("AcDb:ObjFreeSpace", 6, KMaxPageSize, 2),
    ("AcDb:Template", 5, KMaxPageSize, 2),
    ("AcDb:Handles", 4, KMaxPageSize, 2),
    ("AcDb:Classes", 3, KMaxPageSize, 2),
    ("AcDb:AuxHeader", 2, KMaxPageSize, 2),
    ("AcDb:Header", 1, KMaxPageSize, 2),
)

# product text must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KProductText = (
    '<ProductInformation name ="Kit" build_version="1" registry_version="26.0"'
    ' install_id_string="Kit" registry_localeID="1033"/>'
)

# product key must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KProductKey = bytes.fromhex("a93caf13fcf26d4294b93544a31b842f")
