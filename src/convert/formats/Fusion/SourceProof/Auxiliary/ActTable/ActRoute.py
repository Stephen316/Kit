from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole


# route evidence separates the native owner key from the indexed fields record
@MakeDataClass(frozen=True, slots=True)
class ActRoute:
    Key: str
    Prefix: int
    OwnerId: int
    FieldsSpan: RecordSpan
    Roles: tuple[tuple[ActRole, str], ...]
    Residual: int
