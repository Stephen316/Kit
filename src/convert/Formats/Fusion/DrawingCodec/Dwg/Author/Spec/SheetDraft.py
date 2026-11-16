from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Spec.TitleText import TitleText


# sheet draft needs an explicit state contract so drawing objects retain valid ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class SheetDraft:
    LayoutName: str
    TitleTexts: tuple[TitleText, ...] = ()
    SheetSize: str = "A3 Landscape"
