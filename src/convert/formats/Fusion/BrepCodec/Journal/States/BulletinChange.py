from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class BulletinChange:
    OldRef: int
    NewRef: int
