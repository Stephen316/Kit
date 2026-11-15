from dataclasses import dataclass as MakeDataClass


# vertex field needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class VertexField:
    TypeCode: int
    UsageCode: int
    WordOffset: int
    StreamIndex: int
    UsageIndex: int
    InstanceMode: int
