KRange = tuple[float, float]
KRangeLimit = 1e-9


def MergeRanges(Ranges: list[KRange]) -> list[KRange]:
    Merged: list[KRange] = []
    for Lower, Upper in sorted(Ranges):
        if Merged and Lower <= Merged[-1][1] + KRangeLimit:
            Merged[-1] = (Merged[-1][0], max(Merged[-1][1], Upper))
            continue
        Merged.append((Lower, Upper))
    return Merged


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
