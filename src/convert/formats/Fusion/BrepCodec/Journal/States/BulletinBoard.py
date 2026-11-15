from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.States.BulletinChange import (
    BulletinChange,
)


# bulletin board needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class BulletinBoard:
    OwnerNode: int
    Status: int
    Changes: tuple[BulletinChange, ...]
