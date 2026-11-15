from __future__ import annotations

from types import ModuleType

from tools.TestShards.Reuse.Track.ForwardCall import ForwardCall
from tools.TestShards.Reuse.Track.NoteCallMut import NoteCallMut
from tools.TestShards.Reuse.Track.TrackErrors import KTrackErrors
from tools.TestShards.Reuse.Track.TrackState import TrackState


# the import operation needs a consistent construction rule so dependency changes cannot revive stale passing results
def BuildImport(State: TrackState, Original: ForwardCall) -> ForwardCall:

    # the track import contract needs a shared interpretation so dependency changes cannot revive stale passing results
    def TrackImport(*ArgList: object, **KeyArgs: object) -> ModuleType:
        Result = Original(*ArgList, **KeyArgs)
        if not State.Active:
            return Result
        try:
            NoteCallMut(State, ArgList, KeyArgs)
        except KTrackErrors:
            State.Failures += 1
        return Result

    return TrackImport
