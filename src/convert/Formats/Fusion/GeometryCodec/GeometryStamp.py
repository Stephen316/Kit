from dataclasses import dataclass as MakeDataClass


# geometry stamp needs an explicit state contract so geometric values retain their native record boundaries
@MakeDataClass(frozen=True, slots=True)
class GeometryStamp:
    Product: str
    Version: str
    SavedAt: str

    # invalid geometry stamp state must fail at construction so geometry serialization never receives an inconsistent contract
    def __post_init__(self) -> None:
        for Value in (self.Product, self.Version, self.SavedAt):
            if not Value or not Value.isprintable():
                raise ValueError("Geometry provenance must be nonempty printable text")
            if len(Value.encode("utf-8")) > 255:
                raise ValueError("Geometry provenance exceeds its byte-count field")
