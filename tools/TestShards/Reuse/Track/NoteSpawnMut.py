from __future__ import annotations

from tools.TestShards.Reuse.Track.ContextMut import ContextMut
from tools.TestShards.Reuse.Track.FindOpener import FindOpener
from tools.TestShards.Reuse.Track.TrackState import TrackState


# the note spawn contract needs a shared interpretation so dependency changes cannot revive stale passing results
def NoteSpawnMut(State: TrackState) -> None:
    Opener, _ = FindOpener(State.RootText)
    if Opener is not None:
        State.Spawners.add(Opener)
    Record = ContextMut(State)
    if Record is not None:
        Record.Opaque = True
