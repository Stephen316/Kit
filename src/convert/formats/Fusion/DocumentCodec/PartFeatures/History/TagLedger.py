from convert.formats.Fusion.DocumentCodec.PartFeatures.History.FaceKey import FaceKey
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody


# the tag ledger contract needs a dedicated boundary so feature parameters remain connected to the resulting geometry
class TagLedger:

    # tag ledger needs explicit initial state so feature parameters remain connected to the resulting geometry
    def __init__(self) -> None:
        super().__init__()
        self.Tags: dict[tuple[object, ...], int] = {}
        self.LiveKeys: dict[int, set[tuple[object, ...]]] = {}
        self.NextTag = 0

    # the claim contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
    def Claim(self, Identity: tuple[object, ...]) -> int:
        if Identity not in self.Tags:
            self.Tags[Identity] = self.NextTag
            self.NextTag += 1
        return self.Tags[Identity]

    # the face tags contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
    def FaceTags(self, Body: ShapeBody, Ordinal: int) -> dict[tuple[object, ...], int]:
        Previous = self.LiveKeys.get(Ordinal, set())
        Result: dict[tuple[object, ...], int] = {}
        for FaceValue in Body.Faces:
            KeyValue = FaceKey(FaceValue)
            if KeyValue not in Previous:
                _ = self.Tags.pop((Ordinal, KeyValue), None)
            Result[KeyValue] = self.Claim((Ordinal, KeyValue))
        self.LiveKeys[Ordinal] = set(Result)
        return Result
