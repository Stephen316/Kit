from convert.Formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell


# the patch word contract needs a shared interpretation so topology changes retain their native revision relationships
def PatchWord(Number: float) -> str:
    return str(Number) if isinstance(Number, int) else "%.17g" % Number


# the patches operation needs a consistent construction rule so topology changes retain their native revision relationships
def WritePatches(Regions: tuple[tuple[PatchCell, ...], ...]) -> str:
    Lines = ["0 " + str(len(Regions))]
    for Region in Regions:
        Words = [str(len(Region))]
        for CellValue in Region:
            Words.extend(
                PatchWord(Number)
                for Number in (CellValue.Face, *CellValue.Window, *CellValue.Offset)
            )
        Lines.append(" ".join(Words) + " ")
    return "\n".join(Lines) + "\n"
