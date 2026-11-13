from __future__ import annotations

from dataclasses import dataclass as DataClass
from dataclasses import field as DataField


@DataClass(slots=True)
class ModuleDeps:
    Files: set[str] = DataField(default_factory=set[str])
    Folders: set[str] = DataField(default_factory=set[str])
    Opaque: bool = False
