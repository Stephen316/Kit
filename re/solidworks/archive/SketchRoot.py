"""Enter the witnessed equation-bearing configuration through the common part map."""

from dataclasses import replace
from pathlib import Path

from convert.adapters.solidworks.config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.config.RootAtoms import AtomEnd, EndGhosts
from convert.adapters.solidworks.config.RootEntry import FindEntry
from convert.adapters.solidworks.config.RootFields import ModelAtomStart
from convert.adapters.solidworks.config.RootLayout import (
    KConfigGen as KGeneration,
    ExtendRoot,
    LoadPartLayouts,
)
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    LayoutTable,
    ReadTag,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch as Require


# split lengths independently check the body boundary and permit one shared object map
def FindRelations(BlobValue, ModelEntry):
    Cursor, FirstAtom, Count = ModelAtomStart(BlobValue, ModelEntry)
    Require(Count, 2, "guarded atom count")
    FirstTag = ReadTag(BlobValue, FirstAtom)
    Require(
        (FirstTag.kind, FirstTag.class_name),
        (KDefinitionKind, "moAtom_c"),
        "typed first atom",
    )
    NextAtom = AtomEnd(BlobValue, FirstAtom + FirstTag.size)
    NextTag = ReadTag(BlobValue, NextAtom)
    Require(NextTag.kind, KClassRefKind, "typed second atom")
    AtomStop = AtomEnd(BlobValue, NextAtom + NextTag.size)
    Relation = EndGhosts(BlobValue, AtomStop + 4)
    Require(
        ReadTag(BlobValue, Relation).class_name, "moRelMgr_c", "typed relation manager"
    )
    return FirstAtom - Cursor, Relation - AtomStop


# the p04 equation grammar remains in research while the root prefix is shared
def ReadSketchStart(BlobValue):
    Stages = LoadPartLayouts()
    Model, Layouts = ReadModelEntry(BlobValue, Stages)
    AtomRun, RelationRun = FindRelations(BlobValue, Model)
    Relations = LayoutTable.LoadAction(Path(__file__).with_suffix(".json"))
    Layouts = ExtendRoot(
        Layouts, Stages.Atoms, ("moAtom_c", "moAtom_c", "moRelMgr_c"), (AtomRun, 0, RelationRun)
    )
    Layouts = replace(Layouts, classes={**Layouts.classes, **Relations.classes})
    return FindEntry(BlobValue, Layouts, "sgSketch")
