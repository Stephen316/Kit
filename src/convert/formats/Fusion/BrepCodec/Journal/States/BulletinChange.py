from dataclasses import dataclass as MakeDataClass


# bulletin change needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class BulletinChange:
    OldRef: int
    NewRef: int
