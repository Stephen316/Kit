from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class VertexField:
    TypeCode: int
    UsageCode: int
    WordOffset: int
    StreamIndex: int
    UsageIndex: int
    InstanceMode: int
