from __future__ import annotations

from collections.abc import Mapping


def ReadPackage(Globals: Mapping[str, object]) -> str:
    Package = Globals.get("__package__")
    if isinstance(Package, str):
        return Package
    ModName = Globals.get("__name__")
    if not isinstance(ModName, str):
        return ""
    return ModName if "__path__" in Globals else ModName.rpartition(".")[0]
