from __future__ import annotations

from tools.TestShards.Reuse.Track.AuditPath import AuditPath
from tools.TestShards.Reuse.Track.ContextMut import ContextMut
from tools.TestShards.Reuse.Track.FindOpener import FindOpener
from tools.TestShards.Reuse.Track.IsReadOpen import IsReadOpen
from tools.TestShards.Reuse.Track.TrackState import TrackState


def NoteOpenMut(State: TrackState, ArgList: tuple[object, ...]) -> None:
    PathValue, ModeValue, FlagValue = (*ArgList, None, None, None)[:3]
    if PathValue is None or not IsReadOpen(ModeValue, FlagValue):
        return
    RelText = AuditPath(State.RootText, PathValue)
    if not RelText:
        return
    Opener, _ = FindOpener(State.RootText)
    if Opener is not None and Opener != RelText:
        State.Links.setdefault(Opener, set()).add(RelText)
    Record = ContextMut(State)
    if Record is not None:
        Record.Files.add(RelText)
