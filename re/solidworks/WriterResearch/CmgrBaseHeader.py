from dataclasses import dataclass

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

KPreviewOutdated = 0x80
KPreviewMissing = 0x100
KBlankMigrationSeen = 0x400000
KLinkedTreeState = 0x80000000
KStandaloneFlags = (
    KPreviewOutdated | KPreviewMissing | KBlankMigrationSeen | KLinkedTreeState
)


# Distinct native bookkeeping owners provide these evolving words independently.
@dataclass(frozen=True)
class CmgrBaseState:
    model_highest_id: int
    session_stamp: int
    mass_stamp: int


def RequireBaseState(Generation: int, State: CmgrBaseState) -> None:
    RequireArch(
        type(Generation) is int and Generation == 19000,
        True,
        "CMgr standalone base header generation",
    )
    RequireArch(
        all(
            type(word) is int and 0 <= word <= 0xFFFFFFFF
            for word in (State.model_highest_id, State.session_stamp, State.mass_stamp)
        ),
        True,
        "CMgr standalone base header bookkeeping",
    )


# The caller supplies shared model state for the measured standalone archive profile.
def WriteCmgrHeader(
    Writer: ArchiveWriter, Generation: int, State: CmgrBaseState
) -> None:
    RequireBaseState(Generation, State)
    Writer.string("")
    Writer.i32(-1)
    Writer.u32(KStandaloneFlags)
    Writer.string("")
    Writer.u32(State.model_highest_id)
    Writer.u32(State.session_stamp)
    Writer.u32(State.mass_stamp)


# The recorded base flags and absent strings bound the supported archive branch.
def ReadCmgrHeader(Cursor: ArchiveCursor, Generation: int) -> CmgrBaseState:
    RequireArch(Generation, 19000, "CMgr standalone base header generation")
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadInts("<iI"), Cursor.ReadText()),
        ("", (-1, KStandaloneFlags), ""),
        "CMgr standalone base header strings and flags",
    )
    state = CmgrBaseState(*Cursor.ReadInts("<3I"))
    RequireBaseState(Generation, state)
    return state
