from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadPatchRow import (
    ReadPatchRow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.WritePatches import (
    WritePatches,
)


def ReadPatches(ProgramText: str) -> tuple[tuple[PatchCell, ...], ...]:
    Lines = ProgramText.split("\n")
    if not 3 <= len(Lines) <= 4098 or Lines[-1]:
        raise ValueError("Invalid Fusion T-spline patch program extent")
    if Lines[0] != "0 " + str(len(Lines) - 2):
        raise ValueError("Unsupported Fusion T-spline patch program header")
    Regions = tuple(ReadPatchRow(LineText) for LineText in Lines[1:-1])
    if WritePatches(Regions) != ProgramText:
        raise ValueError("Noncanonical Fusion T-spline patch program")
    return Regions
