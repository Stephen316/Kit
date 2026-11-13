from __future__ import annotations

from types import ModuleType

from tools.TestShards.Reuse.Track.ForwardCall import ForwardCall
from tools.TestShards.Reuse.Track.FindOpener import FindOpener
from tools.TestShards.Reuse.Track.ImportedFiles import ImportedFiles
from tools.TestShards.Reuse.Track.NoteImportMut import NoteImportMut
from tools.TestShards.Reuse.Track.TrackErrors import KTrackErrors
from tools.TestShards.Reuse.Track.TrackState import TrackState


def BuildModule(State: TrackState, Original: ForwardCall) -> ForwardCall:
    def TrackModule(*ArgList: object, **KeyArgs: object) -> ModuleType:
        Result = Original(*ArgList, **KeyArgs)
        if not State.Active:
            return Result
        try:
            Located = ImportedFiles(State.RootText, Result.__name__, "", (), 0)
            NoteImportMut(State, Located, FindOpener(State.RootText)[0])
        except KTrackErrors:
            State.Failures += 1
        return Result

    return TrackModule
