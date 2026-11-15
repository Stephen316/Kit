from __future__ import annotations

from tools.TestShards.Reuse.Track.ModuleDeps import ModuleDeps
from tools.TestShards.Reuse.Track.TrackState import TrackState


# the context contract needs a shared interpretation so dependency changes cannot revive stale passing results
def ContextMut(State: TrackState) -> ModuleDeps | None:
    if State.Current is None:
        return None
    Record = State.Modules.get(State.Current)
    if Record is None:
        Record = State.Modules[State.Current] = ModuleDeps()
    return Record
