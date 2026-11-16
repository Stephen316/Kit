from dataclasses import dataclass as Dataclass

from ConfigAtomManager import BossAtomBody, ConfigAtomBinding, WriteConfigAtomManager
from ConfigGhostRelation import GhostRelationSlots, WriteGhostRelationManagers
from PartArchive import PartArchiveWriter


# These slots are shared by the detail and resolved feature writers.
@Dataclass(frozen=True, slots=True)
class ConfigHistory:
    Atom: ConfigAtomBinding | None
    GhostRelation: GhostRelationSlots


# The ordinary second split files the atom and relation records on the first split's map.
def WriteConfigHistory(
    Writer: PartArchiveWriter, Generation: int, Body: BossAtomBody | None
) -> ConfigHistory:
    Atom = WriteConfigAtomManager(Writer, Generation, Body)
    GhostRelation = WriteGhostRelationManagers(
        Writer, Generation, GhostPartitionPopulated=True, AutoSolveOrder=True
    )
    return ConfigHistory(Atom, GhostRelation)
