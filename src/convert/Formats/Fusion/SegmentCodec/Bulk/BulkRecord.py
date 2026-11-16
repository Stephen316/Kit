from dataclasses import dataclass as MakeDataClass


# framing stays independent from the semantic encoder for each record class
@MakeDataClass(frozen=True, slots=True)
class BulkRecord:
    TypeCode: int
    ObjectId: int
    IsPrimary: bool
    Payload: bytes
