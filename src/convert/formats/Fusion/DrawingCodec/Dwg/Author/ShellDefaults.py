from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgCryptHeader import (
    DwgCryptHeader,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader

KAuthorVersion = "AC1032"
KMaxPageSize = 0x7400

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

KProductText = (
    '<ProductInformation name ="Kit" build_version="1" registry_version="26.0"'
    ' install_id_string="Kit" registry_localeID="1033"/>'
)
KProductKey = bytes.fromhex("a93caf13fcf26d4294b93544a31b842f")
