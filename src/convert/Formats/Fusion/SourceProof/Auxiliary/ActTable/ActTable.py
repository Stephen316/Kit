from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole
from convert.Formats.Fusion.SourceProof.Auxiliary.ActTable.ActRoute import ActRoute


# manifest callers need exact snapshot and field identities after validation
@MakeDataClass(frozen=True, slots=True)
class ActTable:
    SnapshotId: str
    HeadId: str
    TableSpan: RecordSpan
    Routes: tuple[ActRoute, ...]
    Roles: tuple[tuple[ActRole, str], ...]
