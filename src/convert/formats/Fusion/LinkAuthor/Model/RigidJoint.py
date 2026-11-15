from dataclasses import dataclass as MakeDataClass


# rigid joint needs an explicit state contract so cross document references retain their intended ownership
@MakeDataClass(frozen=True, slots=True)
class RigidJoint:
    FirstIndex: int
    SecondIndex: int
