from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormFace,
    FormWindow,
)


@MakeDataClass(frozen=True, slots=True)
class FormLabel:
    Label: str
    EntityType: int
    Windows: tuple[FormWindow, ...]


def FaceWindows(Model: FormBody, FaceValue: FormFace) -> tuple[FormWindow, ...]:
    Cells = sorted(
        Model.Regions[FaceValue.Surface.Region], key=lambda CellValue: CellValue.Face
    )
    return tuple(
        FormWindow(
            CellValue.Face,
            float(CellValue.Window[0]),
            float(CellValue.Window[1]),
            float(CellValue.Window[2]),
            float(CellValue.Window[3]),
        )
        for CellValue in Cells
    )


def FormLabels(Model: FormBody) -> tuple[FormLabel, ...]:
    Labels = [
        FormLabel(FaceValue.Label, 0, FaceWindows(Model, FaceValue))
        for FaceValue in Model.Faces
        if FaceValue.Label
    ]
    Labels += [
        FormLabel(EdgeValue.Label, 1, EdgeValue.Windows)
        for EdgeValue in Model.Edges
        if EdgeValue.Label
    ]
    Unique = {LabelValue.Label: LabelValue for LabelValue in reversed(Labels)}
    return tuple(sorted(Unique.values(), key=lambda LabelValue: int(LabelValue.Label)))
