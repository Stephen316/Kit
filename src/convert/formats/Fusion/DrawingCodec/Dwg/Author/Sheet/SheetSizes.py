from dataclasses import dataclass as MakeDataClass
from math import floor as RoundDown

KIsoLargest = (841.0, 1189.0)
KAsmeLargest = (34.0, 44.0)
KIsoFormats = ("A0", "A1", "A2", "A3", "A4")
KAsmeFormats = ("E", "D", "C", "B", "A")
KInchLength = 25.4
KIsoMargin = 10.0
KAsmeMargin = 0.5 * KInchLength
KOrientations = ("Landscape", "Portrait")


@MakeDataClass(frozen=True, slots=True)
class PaperSize:
    FormatName: str
    PaperWidth: float
    PaperHeight: float
    IsMetric: bool

    @property
    def MediaName(self) -> str:
        Family, Suffix = ("ISO", "MM") if self.IsMetric else ("ANSI", "Inches")
        Across, Upward = self.NominalSize
        Sizes = f"({Across:.2f}_x_{Upward:.2f}_{Suffix})"
        return f"{Family}_full_bleed_{self.FormatName}_{Sizes}"

    @property
    def NominalSize(self) -> tuple[float, float]:
        Length = 1.0 if self.IsMetric else KInchLength
        return self.PaperWidth / Length, self.PaperHeight / Length

    @property
    def StandardName(self) -> str:
        return "ISO" if self.IsMetric else "ASME"

    @property
    def FrameMargin(self) -> float:
        return KIsoMargin if self.IsMetric else KAsmeMargin

    @property
    def TitleCorner(self) -> tuple[float, float]:
        return (self.PaperWidth - self.FrameMargin, self.FrameMargin)


def HalvedSides(
    Largest: tuple[float, float], Steps: int, Metric: bool
) -> tuple[float, float]:
    Short, LongSide = Largest
    for _ in range(Steps):
        Halved = LongSide / 2
        Short, LongSide = (float(RoundDown(Halved)) if Metric else Halved), Short
    return Short, LongSide


def SheetSize(SizeName: str) -> PaperSize:
    Parts = SizeName.split(" ")
    if len(Parts) != 2 or Parts[1] not in KOrientations:
        raise ValueError(f"Authored DWG sheet size {SizeName!r} is unsupported")
    FormatName, Orientation = Parts
    if FormatName in KIsoFormats:
        Short, LongSide = HalvedSides(KIsoLargest, KIsoFormats.index(FormatName), True)
        IsMetric = True
    elif FormatName in KAsmeFormats:
        Short, LongSide = HalvedSides(
            KAsmeLargest, KAsmeFormats.index(FormatName), False
        )
        Short, LongSide = Short * KInchLength, LongSide * KInchLength
        IsMetric = False
    else:
        raise ValueError(f"Authored DWG sheet size {SizeName!r} is unsupported")
    if Orientation == "Landscape":
        return PaperSize(FormatName, LongSide, Short, IsMetric)
    return PaperSize(FormatName, Short, LongSide, IsMetric)
