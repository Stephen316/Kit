from __future__ import annotations

from tools.TestShards.Reuse.Track.ContextMut import ContextMut
from tools.TestShards.Reuse.Track.TrackState import TrackState


def NoteImportMut(
    State: TrackState, Located: tuple[str, ...], Importer: str | None
) -> None:
    if not Located:
        return
    if Importer is not None:
        State.Links.setdefault(Importer, set()).update(
            PathText for PathText in Located if PathText != Importer
        )
    Record = ContextMut(State)
    if Record is not None:
        Record.Files.update(Located)
