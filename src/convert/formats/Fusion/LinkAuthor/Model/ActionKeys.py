from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ActionKeys:
    Feature: int
    FeatureData: int
    Status: int
    Table: int
    FeatureId: int
    FeatureIndex: int
    Extra: tuple[int, ...]
