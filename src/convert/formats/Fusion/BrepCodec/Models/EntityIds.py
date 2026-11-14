from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


@MakeDataClass(frozen=True, slots=True)
class EntityIds:
    FaceIds: tuple[int, ...] = (-1, -1, -1)
    VertexIds: tuple[int, ...] = (-1, -1)

    def __post_init__(self) -> None:
        if len(self.FaceIds) != 3 or len(self.VertexIds) != 2:
            raise ValueError(
                "Fusion BRep entity identities need three faces and two vertices"
            )
        for IdValue in (*self.FaceIds, *self.VertexIds):
            CheckInteger(IdValue, "entity identity", Lower=-1, Upper=(1 << 31) - 1)
