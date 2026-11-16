from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Sheet.BorderPlan import (
    KPointPair,
    KSegment,
)

# title width must remain consistent across callers so paper layouts retain consistent object ownership
KTitleWidth = 180.0

# row height must remain consistent across callers so paper layouts retain consistent object ownership
KRowHeight = 8.0

# cell inset must remain consistent across callers so paper layouts retain consistent object ownership
KCellInset = 1.0

# value drop must remain consistent across callers so paper layouts retain consistent object ownership
KValueDrop = 3.0

# label height must remain consistent across callers so paper layouts retain consistent object ownership
KLabelHeight = 1.8

# value height must remain consistent across callers so paper layouts retain consistent object ownership
KValueHeight = 2.5

# large height must remain consistent across callers so paper layouts retain consistent object ownership
KLargeHeight = 3.5

# the large fields order must stay explicit so paper layouts retain consistent object ownership
KLargeFields = ("TITLE_1", "DRAWING_NUMBER")

# the title rows order must stay explicit so paper layouts retain consistent object ownership
KTitleRows: tuple[tuple[tuple[str, str, float], ...], ...] = (
    (
        ("DEPT", "Responsible department", 45.0),
        ("TECHNICAL_REFERENCE", "Technical reference", 45.0),
        ("DOCUMENT_TYPE", "Document type", 45.0),
        ("DOCUMENT_STATUS", "Document status", 45.0),
    ),
    (
        ("CREATED_BY", "Created by", 45.0),
        ("APPROVED_BY", "Approved by", 45.0),
        ("TITLE_1", "Title", 90.0),
    ),
    (
        ("CREATED_DATE", "Created date", 45.0),
        ("APPROVED_DATE", "Approval date", 45.0),
        ("TITLE_2", "Supplementary title", 90.0),
    ),
    (
        ("DRAWING_NUMBER", "Identification number", 90.0),
        ("TITLE_3", "Supplementary title", 90.0),
    ),
    (
        ("REV", "Revision", 45.0),
        ("DATE_OF_ISSUE", "Date of issue", 90.0),
        ("SHEET", "Sheet", 45.0),
    ),
)


# title field needs an explicit state contract so paper layouts retain consistent object ownership
@MakeDataClass(frozen=True, slots=True)
class TitleField:
    Tag: str
    Prompt: str
    LabelCorner: KPointPair
    ValueCorner: KPointPair
    ValueHeight: float


# title plan needs an explicit state contract so paper layouts retain consistent object ownership
@MakeDataClass(frozen=True, slots=True)
class TitlePlan:
    Lines: tuple[KSegment, ...]
    Fields: tuple[TitleField, ...]


# the row fields contract needs a shared interpretation so paper layouts retain consistent object ownership
def RowFields(
    Cells: tuple[tuple[str, str, float], ...], Upper: float
) -> list[TitleField]:
    Fields: list[TitleField] = []
    Across = -KTitleWidth
    for FieldTag, Prompt, Width in Cells:
        Height = KLargeHeight if FieldTag in KLargeFields else KValueHeight
        Fields.append(
            TitleField(
                FieldTag,
                Prompt,
                (Across + KCellInset, Upper - KCellInset),
                (Across + KCellInset, Upper - KValueDrop),
                Height,
            )
        )
        Across += Width
    return Fields


# the row lines contract needs a shared interpretation so paper layouts retain consistent object ownership
def RowLines(Cells: tuple[tuple[str, str, float], ...], Lower: float) -> list[KSegment]:
    Lines: list[KSegment] = []
    Across = -KTitleWidth
    for _, _, Width in Cells[:-1]:
        Across += Width
        Lines.append(((Across, Lower), (Across, Lower + KRowHeight)))
    return Lines


# the plan title contract needs a stable decomposition so paper layouts retain consistent object ownership
def PlanTitle() -> TitlePlan:
    Total = KRowHeight * len(KTitleRows)
    Lines: list[KSegment] = [
        ((-KTitleWidth, 0.0), (0.0, 0.0)),
        ((0.0, 0.0), (0.0, Total)),
        ((0.0, Total), (-KTitleWidth, Total)),
        ((-KTitleWidth, Total), (-KTitleWidth, 0.0)),
    ]
    Fields: list[TitleField] = []
    for Index, Cells in enumerate(KTitleRows):
        Upper = Total - Index * KRowHeight
        Lower = Upper - KRowHeight
        if Index:
            Lines.append(((-KTitleWidth, Upper), (0.0, Upper)))
        Lines.extend(RowLines(Cells, Lower))
        Fields.extend(RowFields(Cells, Upper))
    return TitlePlan(tuple(Lines), tuple(Fields))
