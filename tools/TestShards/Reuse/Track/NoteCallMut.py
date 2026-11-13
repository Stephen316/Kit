from __future__ import annotations

import os as OsLib
from collections.abc import Mapping, Sequence
from typing import cast as CastValue

from tools.TestShards.Reuse.Track.FindOpener import FindOpener
from tools.TestShards.Reuse.Track.ImportedFiles import ImportedFiles
from tools.TestShards.Reuse.Track.LocateFile import LocateFile
from tools.TestShards.Reuse.Track.NoteImportMut import NoteImportMut
from tools.TestShards.Reuse.Track.ReadPackage import ReadPackage
from tools.TestShards.Reuse.Track.TrackState import TrackState

KImportFields = ("name", "globals", "locals", "fromlist", "level")


def NoteCallMut(
    State: TrackState, ArgList: tuple[object, ...], KeyArgs: Mapping[str, object]
) -> None:
    Fields = {**dict(zip(KImportFields, ArgList)), **KeyArgs}
    NameText = Fields.get("name")
    Level = Fields.get("level") or 0
    GlobalMap = Fields.get("globals")
    FromList = Fields.get("fromlist") or ()
    if not isinstance(NameText, str) or not isinstance(Level, int):
        return
    Globals = (
        CastValue(dict[str, object], GlobalMap) if isinstance(GlobalMap, dict) else {}
    )
    Members = (
        tuple(
            Member
            for Member in CastValue(Sequence[object], FromList)
            if isinstance(Member, str)
        )
        if isinstance(FromList, (list, tuple))
        else ()
    )
    Package = ReadPackage(Globals) if Level else ""
    Located = ImportedFiles(State.RootText, NameText, Package, Members, Level)
    if not Located:
        return
    FileText = Globals.get("__file__")
    Importer = (
        LocateFile(State.RootText, OsLib.path.abspath(FileText))
        if isinstance(FileText, str)
        else None
    )
    NoteImportMut(State, Located, Importer or FindOpener(State.RootText)[0])
