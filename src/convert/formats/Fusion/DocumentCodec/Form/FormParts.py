from dataclasses import dataclass as MakeDataClass
from uuid import uuid4 as MakeUuid


# form parts needs an explicit state contract so editable control cages retain their document relationships
@MakeDataClass(frozen=True, slots=True)
class FormParts:
    History: str
    Snapshot: str
    Cage: str


# the form parts operation needs a consistent construction rule so editable control cages retain their document relationships
def MakeFormParts() -> FormParts:
    return FormParts(
        "BREP." + str(MakeUuid()) + ".smbh",
        "BREP." + str(MakeUuid()) + ".smb",
        "TSpline." + str(MakeUuid()) + ".tsm",
    )
