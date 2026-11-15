"""Replay the configuration map for rectangle parts without saved equations."""

from ArchiveVersion import KApplicationBuild
from ConfigPresentation import ReadModelPresentation
from SketchCursor import SketchCursor
from SketchRoot import (
    AtomEnd,
    EndGhosts,
    FindEntry,
    KRootClass,
    ModelAtomStart,
    ReadModelEntry,
    Require,
)
from convert.adapters.solidworks.container.Archive import KDefinitionKind, ReadTag


# the zero- and one-atom model branches share the actual root allocations
def read_rectangle_configuration(blob, build):
    Require(build, KApplicationBuild, "witnessed rectangular model build")
    model, stages = ReadModelEntry(blob)
    model_body, atom, count = ModelAtomStart(blob, model)
    Require(count in (0, 1), True, "rectangle configuration atom count")
    classes = stages["prefix"]
    root = classes[KRootClass]
    classes.update(stages["relations"])
    cursor = model_body
    if count:
        tag = ReadTag(blob, atom)
        Require((tag.kind, tag.class_name), (KDefinitionKind, "moAtom_c"), "typed rectangle body atom")
        root["child_slots"].append("moAtom_c")
        root["runs"]["9"] = atom - model_body
        cursor = AtomEnd(blob, atom + tag.size)
    relation = EndGhosts(blob, (cursor if count else atom) + 4)
    root["child_slots"].append("moRelMgr_c")
    root["runs"][str(9 + count)] = relation - cursor
    manager = FindEntry(blob, classes, "moRelMgr_c")
    Require(manager.offset, relation, "typed relation manager boundary")
    archive = SketchCursor(blob, manager, None)
    Require(archive.ReadValue("<2H"), (0, 0), "empty equations and parameters")
    Require(archive.ReadText(), "", "empty relation manager label")
    Require(archive.ReadValue("<4i"), (0, 0, 1, -1), "ordinary relation manager state")
    Require(archive.ReadValue("<Hii"), (0, -1, 0), "empty relation manager tails")
    events, regions = ReadModelPresentation(archive)
    return archive, {"atom_count": count, "relation_manager": relation, "pointers": events, "regions": regions}
