# the range shape must stay shared so parametric feature reconstruction uses one contract for compatible values
KRange = tuple[float, float]

# the range limit tolerance prevents rounding noise from creating false geometric distinctions during reconstruction
KRangeLimit = 1e-9


# the merge ranges contract needs a stable decomposition so feature parameters remain connected to the resulting geometry
def MergeRanges(Ranges: list[KRange]) -> list[KRange]:
    Merged: list[KRange] = []
    for Lower, Upper in sorted(Ranges):
        if Merged and Lower <= Merged[-1][1] + KRangeLimit:
            Merged[-1] = (Merged[-1][0], max(Merged[-1][1], Upper))
            continue
        Merged.append((Lower, Upper))
    return Merged


# the range minus contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def RangeMinus(Ranges: list[KRange], Removed: list[KRange]) -> list[KRange]:
    Result: list[KRange] = []
    for Lower, Upper in MergeRanges(Ranges):
        Cursor = Lower
        for Start, Finish in MergeRanges(Removed):
            if Finish <= Cursor + KRangeLimit or Start >= Upper - KRangeLimit:
                continue
            if Start > Cursor + KRangeLimit:
                Result.append((Cursor, Start))
            Cursor = max(Cursor, Finish)
        if Upper > Cursor + KRangeLimit:
            Result.append((Cursor, Upper))
    return Result


# the split ranges contract needs a stable decomposition so feature parameters remain connected to the resulting geometry
def SplitRanges(Ranges: list[KRange], CutValues: list[float]) -> list[KRange]:
    Result: list[KRange] = []
    for Lower, Upper in Ranges:
        Inner = {
            round(CutValue, 9): CutValue
            for CutValue in CutValues
            if Lower + KRangeLimit < CutValue < Upper - KRangeLimit
        }
        Bounds = [Lower, *(Inner[KeyValue] for KeyValue in sorted(Inner)), Upper]
        Result.extend(zip(Bounds, Bounds[1:]))
    return Result
