from dataclasses import dataclass as MakeDataClass


# action keys needs an explicit state contract so cross document references retain their intended ownership
@MakeDataClass(frozen=True, slots=True)
class ActionKeys:
    Feature: int
    FeatureData: int
    Status: int
    Table: int
    FeatureId: int
    FeatureIndex: int
    Extra: tuple[int, ...]
