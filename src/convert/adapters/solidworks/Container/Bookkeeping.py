from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from convert.adapters.solidworks.Container.Archive import EncodeNull, EncodeString
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

# configuration object references save in their own named member
KConfigObjects = "Contents/CnfgObjs"

# document clocks share the stamps member used by configuration readers
KModelStamps = "ModelStamps"

# display update readers select the member by the model generation
KDisplayUpdate = "_DL_VERSION_19000/DLUpdateStamp"


# creation and both model counters have separate owners in the document header
@Dataclass(frozen=True)
class PartStamps:
    creation_time: int
    update: int
    body: int


# the ordinary part has no extra configuration object or display update pointer
def EncodePartBookkeeping(Generation: int, Stamps: PartStamps) -> dict[str, bytes]:
    RequireArch(Generation, 19000, "ordinary part bookkeeping generation")
    RequireArch(
        type(Stamps.creation_time) is int and 0 < Stamps.creation_time <= 0x7FFFFFFF,
        True,
        "positive archive creation time",
    )
    RequireArch(
        all(
            type(Value) is int and 0 <= Value <= 0xFFFFFFFF
            for Value in (Stamps.update, Stamps.body)
        ),
        True,
        "unsigned model counters",
    )
    Names = EncodeString("") * 2
    return {
        KConfigObjects: PackFields("<H", 0) + EncodeNull() + Names,
        KModelStamps: PackFields(
            "<3I", Stamps.creation_time, Stamps.update, Stamps.body
        ),
        KDisplayUpdate: PackFields("<I", Stamps.update) + EncodeNull(),
    }
