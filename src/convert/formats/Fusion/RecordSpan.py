from dataclasses import dataclass as Dataclass


# downstream feature decoding needs stable class identities and native record bounds
@Dataclass(frozen=True, slots=True)
class RecordSpan:
    StartOffset: int
    PayloadOffset: int
    EndOffset: int
    ObjectId: int
    TypeCode: int
    ClassGuid: str
    ClassSpace: str
    IsPrimary: bool
