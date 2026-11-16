# the knot spans contract needs a shared interpretation so control cage contributions retain their intended weights
def KnotSpans(Knots: list[float], Degree: int) -> dict[tuple[float, float], int]:
    return {
        (Knots[SpanIndex], Knots[SpanIndex + 1]): SpanIndex
        for SpanIndex in range(Degree, len(Knots) - Degree - 1)
        if Knots[SpanIndex] < Knots[SpanIndex + 1]
    }
