from convert.formats.Fusion.TSplineCodec.Model.IndexPair import IndexPair


def WritePairs(Selector: str, Pairs: tuple[IndexPair, ...]) -> str:
    return (
        "105a "
        + Selector
        + "".join(
            "  " + str(Value.SourceIndex) + " " + str(Value.TargetIndex)
            for Value in Pairs
        )
    )
