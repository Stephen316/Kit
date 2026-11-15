from convert.formats.Fusion.TSplineCodec.Model.IndexPair import IndexPair


# the pairs operation needs a consistent construction rule so control cage topology retains its native connectivity
def WritePairs(Selector: str, Pairs: tuple[IndexPair, ...]) -> str:
    return (
        "105a "
        + Selector
        + "".join(
            "  " + str(Value.SourceIndex) + " " + str(Value.TargetIndex)
            for Value in Pairs
        )
    )
