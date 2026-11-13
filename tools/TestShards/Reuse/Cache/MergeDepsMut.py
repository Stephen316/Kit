from __future__ import annotations

from collections.abc import Mapping

from tools.TestShards.Reuse.Cache.DepGraph import DepGraph
from tools.TestShards.Reuse.Cache.ReadObject import ReadObject
from tools.TestShards.Reuse.Cache.ReadStrings import ReadStrings
from tools.TestShards.Reuse.Track.ModuleDeps import ModuleDeps


def MergeDepsMut(Graph: DepGraph, Payload: Mapping[str, object]) -> None:
    PythonText = Payload.get("Python")
    if not isinstance(PythonText, str):
        raise ValueError("a dependency record has no Python version")
    Graph.Pythons.add(PythonText)
    if Payload.get("Failures") != 0:
        Graph.Failed.append(str(Payload.get("Worker")))
    for ModKey, Entry in ReadObject(Payload.get("Modules"), "Modules").items():
        Fields = ReadObject(Entry, ModKey)
        Record = Graph.Modules.setdefault(ModKey, ModuleDeps())
        Record.Files.update(ReadStrings(Fields.get("Files"), ModKey))
        Record.Folders.update(ReadStrings(Fields.get("Folders"), ModKey))
        Record.Opaque = Record.Opaque or Fields.get("Opaque") is True
    for Section, Target in (("Links", Graph.Links), ("Listers", Graph.Listers)):
        for Source, Targets in ReadObject(Payload.get(Section), Section).items():
            Target.setdefault(Source, set()).update(ReadStrings(Targets, Source))
    Graph.Spawners.update(ReadStrings(Payload.get("Spawners"), "Spawners"))
