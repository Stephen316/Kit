from dataclasses import dataclass as MakeDataClass


# counted text needs an explicit state contract so geometric values retain their native record boundaries
@MakeDataClass(frozen=True, slots=True)
class CountedText:
    Value: str
