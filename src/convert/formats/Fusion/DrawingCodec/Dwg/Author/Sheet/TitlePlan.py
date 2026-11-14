from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.BorderPlan import (
    KPointPair,
    KSegment,
)

KTitleWidth = 180.0
KRowHeight = 8.0
KCellInset = 1.0
KValueDrop = 3.0
KLabelHeight = 1.8
KValueHeight = 2.5
KLargeHeight = 3.5
KLargeFields = ("TITLE_1", "DRAWING_NUMBER")
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


@MakeDataClass(frozen=True, slots=True)
class TitleField:
    Tag: str
    Prompt: str
    LabelCorner: KPointPair
    ValueCorner: KPointPair
    ValueHeight: float


@MakeDataClass(frozen=True, slots=True)
class TitlePlan:
    Lines: tuple[KSegment, ...]
    Fields: tuple[TitleField, ...]


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


def RowLines(Cells: tuple[tuple[str, str, float], ...], Lower: float) -> list[KSegment]:
    Lines: list[KSegment] = []
    Across = -KTitleWidth
    for _, _, Width in Cells[:-1]:
        Across += Width
        Lines.append(((Across, Lower), (Across, Lower + KRowHeight)))
    return Lines


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
