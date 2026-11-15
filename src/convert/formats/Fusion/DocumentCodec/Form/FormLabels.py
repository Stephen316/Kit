from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormFace,
    FormWindow,
)


# form label needs an explicit state contract so editable control cages retain their document relationships
@MakeDataClass(frozen=True, slots=True)
class FormLabel:
    Label: str
    EntityType: int
    Windows: tuple[FormWindow, ...]


# the face windows contract needs a shared interpretation so editable control cages retain their document relationships
def FaceWindows(Model: FormBody, FaceValue: FormFace) -> tuple[FormWindow, ...]:

    # ordering by cell value face must stay deterministic so form feature reconstruction resolves equivalent inputs consistently
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


# the form labels contract needs a shared interpretation so editable control cages retain their document relationships
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

    # ordering by int label value label must stay deterministic so form feature reconstruction resolves equivalent inputs consistently
    return tuple(sorted(Unique.values(), key=lambda LabelValue: int(LabelValue.Label)))
