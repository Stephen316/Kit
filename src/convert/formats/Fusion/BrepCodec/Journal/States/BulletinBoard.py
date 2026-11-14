from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.States.BulletinChange import (
    BulletinChange,
)


@MakeDataClass(frozen=True, slots=True)
class BulletinBoard:
    OwnerNode: int
    Status: int
    Changes: tuple[BulletinChange, ...]
