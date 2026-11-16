from convert.Formats.Fusion.EntityCodec.Limits import KMaxCount


# the value quota contract needs a dedicated boundary so entity identifiers retain their schema and reference meaning
class ValueQuota:

    # value quota needs explicit initial state so entity identifiers retain their schema and reference meaning
    def __init__(self) -> None:
        super().__init__()
        self.Consumed = 0

    # the value operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
    def TakeValue(self) -> None:
        self.TakeMany(1)

    # the many operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
    def TakeMany(self, Count: int) -> None:
        if type(Count) is not int or Count < 0:
            raise ValueError("Fusion entity value count must be nonnegative")
        self.Consumed += Count
        if self.Consumed > KMaxCount:
            raise ValueError("Fusion entity record exceeds the value count limit")
