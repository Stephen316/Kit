from __future__ import annotations

from dataclasses import dataclass as DataClass
from dataclasses import field as DataField

from tools.TestShards.Reuse.Track.ForwardCall import ForwardCall
from tools.TestShards.Reuse.Track.ModuleDeps import ModuleDeps


@DataClass(slots=True)
class TrackState:
    RootText: str
    ImportFunc: ForwardCall
    ModuleFunc: ForwardCall
    Current: str | None = None
    Active: bool = True
    Failures: int = 0
    Modules: dict[str, ModuleDeps] = DataField(default_factory=dict[str, ModuleDeps])
    Links: dict[str, set[str]] = DataField(default_factory=dict[str, set[str]])
    Listers: dict[str, set[str]] = DataField(default_factory=dict[str, set[str]])
    Spawners: set[str] = DataField(default_factory=set[str])
