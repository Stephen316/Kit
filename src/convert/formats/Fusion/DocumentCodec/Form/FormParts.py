from dataclasses import dataclass as MakeDataClass
from uuid import uuid4 as MakeUuid


@MakeDataClass(frozen=True, slots=True)
class FormParts:
    History: str
    Snapshot: str
    Cage: str


def MakeFormParts() -> FormParts:
    return FormParts(
        "BREP." + str(MakeUuid()) + ".smbh",
        "BREP." + str(MakeUuid()) + ".smb",
        "TSpline." + str(MakeUuid()) + ".tsm",
    )
