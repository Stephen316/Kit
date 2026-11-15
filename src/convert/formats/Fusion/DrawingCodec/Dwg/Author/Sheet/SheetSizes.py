from dataclasses import dataclass as MakeDataClass
from math import floor as RoundDown

# the iso largest order must stay explicit so paper layouts retain consistent object ownership
KIsoLargest = (841.0, 1189.0)

# the asme largest order must stay explicit so paper layouts retain consistent object ownership
KAsmeLargest = (34.0, 44.0)

# the iso formats order must stay explicit so paper layouts retain consistent object ownership
KIsoFormats = ("A0", "A1", "A2", "A3", "A4")

# the asme formats order must stay explicit so paper layouts retain consistent object ownership
KAsmeFormats = ("E", "D", "C", "B", "A")

# inch length needs one explicit bound so drawing sheet authoring cannot accept inconsistent resource or layout limits
KInchLength = 25.4

# iso margin must remain consistent across callers so paper layouts retain consistent object ownership
KIsoMargin = 10.0

# asme margin must remain consistent across callers so paper layouts retain consistent object ownership
KAsmeMargin = 0.5 * KInchLength

# the orientations order must stay explicit so paper layouts retain consistent object ownership
KOrientations = ("Landscape", "Portrait")


# paper size needs an explicit state contract so paper layouts retain consistent object ownership
@MakeDataClass(frozen=True, slots=True)
class PaperSize:
    FormatName: str
    PaperWidth: float
    PaperHeight: float
    IsMetric: bool

    # the media name contract needs a shared interpretation so paper layouts retain consistent object ownership
    @property
    def MediaName(self) -> str:
        Family, Suffix = ("ISO", "MM") if self.IsMetric else ("ANSI", "Inches")
        Across, Upward = self.NominalSize
        Sizes = f"({Across:.2f}_x_{Upward:.2f}_{Suffix})"
        return f"{Family}_full_bleed_{self.FormatName}_{Sizes}"

    # the nominal size contract needs a shared interpretation so paper layouts retain consistent object ownership
    @property
    def NominalSize(self) -> tuple[float, float]:
        Length = 1.0 if self.IsMetric else KInchLength
        return self.PaperWidth / Length, self.PaperHeight / Length

    # the standard name contract needs a shared interpretation so paper layouts retain consistent object ownership
    @property
    def StandardName(self) -> str:
        return "ISO" if self.IsMetric else "ASME"

    # the frame margin contract needs a shared interpretation so paper layouts retain consistent object ownership
    @property
    def FrameMargin(self) -> float:
        return KIsoMargin if self.IsMetric else KAsmeMargin

    # the title corner contract needs a shared interpretation so paper layouts retain consistent object ownership
    @property
    def TitleCorner(self) -> tuple[float, float]:
        return (self.PaperWidth - self.FrameMargin, self.FrameMargin)


# the halved sides contract needs a shared interpretation so paper layouts retain consistent object ownership
def HalvedSides(
    Largest: tuple[float, float], Steps: int, Metric: bool
) -> tuple[float, float]:
    Short, LongSide = Largest
    for _ in range(Steps):
        Halved = LongSide / 2
        Short, LongSide = (float(RoundDown(Halved)) if Metric else Halved), Short
    return Short, LongSide


# sheet size needs an explicit validity boundary so paper layouts retain consistent object ownership
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
