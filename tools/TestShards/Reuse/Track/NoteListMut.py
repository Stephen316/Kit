from __future__ import annotations

from tools.TestShards.Reuse.Track.AuditPath import AuditPath
from tools.TestShards.Reuse.Track.ContextMut import ContextMut
from tools.TestShards.Reuse.Track.FindOpener import FindOpener
from tools.TestShards.Reuse.Track.TrackState import TrackState


def NoteListMut(State: TrackState, ArgList: tuple[object, ...]) -> None:
    PathValue = ArgList[0] if ArgList and ArgList[0] is not None else "."
    RelText = AuditPath(State.RootText, PathValue)
    if RelText is None:
        return
    Opener, Importing = FindOpener(State.RootText)
    if Importing:
        return
    if Opener is not None:
        State.Listers.setdefault(Opener, set()).add(RelText)
    Record = ContextMut(State)
    if Record is not None:
        Record.Folders.add(RelText)
