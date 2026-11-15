def KnotSpans(Knots: list[float], Degree: int) -> dict[tuple[float, float], int]:
    return {
        (Knots[SpanIndex], Knots[SpanIndex + 1]): SpanIndex
        for SpanIndex in range(Degree, len(Knots) - Degree - 1)
        if Knots[SpanIndex] < Knots[SpanIndex + 1]
    }
