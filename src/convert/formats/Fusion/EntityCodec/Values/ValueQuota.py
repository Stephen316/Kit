from convert.formats.Fusion.EntityCodec.Limits import KMaxCount


class ValueQuota:
    def __init__(self) -> None:
        super().__init__()
        self.Consumed = 0

    def TakeValue(self) -> None:
        self.TakeMany(1)

    def TakeMany(self, Count: int) -> None:
        if type(Count) is not int or Count < 0:
            raise ValueError("Fusion entity value count must be nonnegative")
        self.Consumed += Count
        if self.Consumed > KMaxCount:
            raise ValueError("Fusion entity record exceeds the value count limit")
