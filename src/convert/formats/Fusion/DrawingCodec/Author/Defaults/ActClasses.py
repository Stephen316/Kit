from convert.formats.Fusion.DrawingCodec.Author.Model.ClassRow import ClassRow

KActClasses = (
    ClassRow(
        "596618BE-CD74-4BC9-A627-2DA799696C2D",
        "E47053DB-8AF6-4521-81D6-523964C0C97A",
        1,
        "ACT",
    ),
    ClassRow(
        "E47053DB-8AF6-4521-81D6-523964C0C97A",
        "CB844AB6-240D-4fc9-9C9F-3679DC896D6F",
        0,
        "DataModel",
    ),
    ClassRow(
        "CB844AB6-240D-4fc9-9C9F-3679DC896D6F",
        "98542EB9-A4F2-4137-A808-DBB5B3CD6159",
        1,
        "DataModel",
    ),
    ClassRow("98542EB9-A4F2-4137-A808-DBB5B3CD6159", "", 0, ""),
    ClassRow(
        "D956D02C-2806-4E57-8B2E-EFA323A5C2B8",
        "CB844AB6-240D-4fc9-9C9F-3679DC896D6F",
        1,
        "ACT",
    ),
    ClassRow(
        "F3E2665C-F3E1-4BA7-8676-8B90579B56D3",
        "E47053DB-8AF6-4521-81D6-523964C0C97A",
        2,
        "ACT",
    ),
    ClassRow(
        "96E1B59A-1989-4493-AA92-67E6072135F6",
        "CB844AB6-240D-4fc9-9C9F-3679DC896D6F",
        1,
        "ACT",
    ),
    ClassRow(
        "F01D16CF-95D5-4239-A488-00448AC88023",
        "834C9DEF-4C39-4587-A08D-A5BD1267B7B4",
        1,
        "ACT",
    ),
    ClassRow(
        "834C9DEF-4C39-4587-A08D-A5BD1267B7B4",
        "CB844AB6-240D-4fc9-9C9F-3679DC896D6F",
        2,
        "DataModel",
    ),
    ClassRow("3AFBE085-BFA1-4DA6-BE71-45A6C61ECB99", "", 1, ""),
)

KActOrder = tuple(RowValue.ClassGuid for RowValue in KActClasses)
