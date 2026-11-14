from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KModelSpace,
    KPaperNetwork,
    KPaperSpace,
)


@MakeDataClass(frozen=True, slots=True)
class ViewKeys:
    Inner: str
    Outer: str
    InnerRef: str
    ModelRef: str
    Frame: str
    Port: str
    Drawing: str
    Action: str
    Body: str
    ViewRep: str


def MakeKeys(Index: int) -> ViewKeys:
    NameText = f"View{Index}"
    Action = f"{KPaperNetwork}/{NameText}"
    return ViewKeys(
        f"BLOCK_HEADER:{NameText}/Inner",
        f"BLOCK_HEADER:{NameText}/Outer",
        f"BLOCK_HEADER:{NameText}/Outer/Ref",
        f"{KModelSpace}/{NameText}",
        f"{KPaperSpace}/{NameText}/Frame",
        f"{KPaperSpace}/{NameText}/Port",
        f"{KPaperSpace}/{NameText}",
        Action,
        Action + "/Body",
        Action + "/Body/Rep",
    )
