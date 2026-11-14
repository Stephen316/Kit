from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class RigidJoint:
    FirstIndex: int
    SecondIndex: int
