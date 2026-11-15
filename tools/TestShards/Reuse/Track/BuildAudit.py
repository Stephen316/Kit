from __future__ import annotations

from collections.abc import Callable

from tools.TestShards.Reuse.Track.NoteListMut import NoteListMut
from tools.TestShards.Reuse.Track.NoteOpenMut import NoteOpenMut
from tools.TestShards.Reuse.Track.NoteSpawnMut import NoteSpawnMut
from tools.TestShards.Reuse.Track.TrackErrors import KTrackErrors
from tools.TestShards.Reuse.Track.TrackState import TrackState

# the list events vocabulary must stay centralized so test reuse agrees on supported native identities
KListEvents = frozenset({"os.listdir", "os.scandir"})

# the spawn events vocabulary must stay centralized so test reuse agrees on supported native identities
KSpawnEvents = frozenset(
    {
        "os.exec",
        "os.fork",
        "os.forkpty",
        "os.posix_spawn",
        "os.spawn",
        "os.startfile",
        "os.system",
        "pty.spawn",
        "subprocess.Popen",
    }
)


# the audit operation needs a consistent construction rule so dependency changes cannot revive stale passing results
def BuildAudit(State: TrackState) -> Callable[[str, tuple[object, ...]], None]:

    # the handle audit contract needs a shared interpretation so dependency changes cannot revive stale passing results
    def HandleAudit(EventName: str, ArgList: tuple[object, ...]) -> None:
        IsOpen = EventName == "open"
        IsList = EventName in KListEvents
        if not State.Active or not (IsOpen or IsList or EventName in KSpawnEvents):
            return
        try:
            if IsOpen:
                NoteOpenMut(State, ArgList)
            elif IsList:
                NoteListMut(State, ArgList)
            else:
                NoteSpawnMut(State)
        except KTrackErrors:
            State.Failures += 1

    return HandleAudit
