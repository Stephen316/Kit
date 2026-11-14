from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.TitleText import TitleText


@MakeDataClass(frozen=True, slots=True)
class SheetDraft:
    LayoutName: str
    TitleTexts: tuple[TitleText, ...] = ()
    SheetSize: str = "A3 Landscape"
