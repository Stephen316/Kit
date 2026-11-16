from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from CmgrInherited import ArchiveFeature, CheckArcFeature, WriteArcFeature
from ConfigAtomManager import ConfigAtomBinding, KAtomClass, RequireBossBody
from PartArchive import PartArchiveWriter
from RectangleTrim import KProfileClass
from ResolvedFolders import CheckFolderMap, WriteFolderName
from convert.adapters.solidworks.Container.Archive import EncodeNull, EncodeString
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import KExtObjectClass
from convert.adapters.solidworks.Resolved.BossChooser import ChooserOwner

KBossClass = "moExtrusion_c"
KBossFlags = (0x40000140, 0xC0000140)


# the boss has its own saved name, visibility state and inherited update fields
@Dataclass(frozen=True, slots=True)
class BossOpening:
    Name: str
    NodeFlags: int
    Feature: ArchiveFeature


# the single ordinary boss must refer to the actual preceding profile, trim and atom
def CheckBossOpen(
    Writer: PartArchiveWriter,
    Generation: int,
    ProfileObject: int,
    FileObject: int,
    Atom: ConfigAtomBinding,
    State: BossOpening,
) -> None:
    CheckFolderMap(Writer, (KBossClass,), 3)
    CheckArcFeature(Generation, State.Feature, AllowRegenTime=True)
    RequireBossBody(Atom.Body)
    RequireArch(
        all(
            Writer.objects.get(Index) == ClassName
            and Index == Writer.classes.get(ClassName, 0) + 1
            for Index, ClassName in (
                (ProfileObject, KProfileClass),
                (FileObject, KExtObjectClass),
                (Atom.ObjectIndex, KAtomClass),
            )
        )
        and sum(Name == KAtomClass for Name in Writer.objects.values()) == 1
        and 0 < Atom.ObjectIndex < ProfileObject < FileObject < Writer.next_index,
        True,
        "owned ordinary boss archive objects",
    )
    RequireArch(
        type(Atom.AtomId) is int and 0 < Atom.AtomId <= 0x7FFFFFFF,
        True,
        "configured native atom ID",
    )
    RequireArch(
        State.NodeFlags in KBossFlags and bool(State.Name) and "\0" not in State.Name,
        True,
        "ordinary boss name and node flags",
    )


# one shared archive map carries the selected profile and generated transfer atom
def WriteBossOpen(
    Writer: PartArchiveWriter,
    Generation: int,
    ProfileObject: int,
    FileObject: int,
    Atom: ConfigAtomBinding,
    State: BossOpening,
) -> ChooserOwner:
    CheckBossOpen(Writer, Generation, ProfileObject, FileObject, Atom, State)
    Name = EncodeString(State.Name)
    FeatureId = Atom.Body.FeatureId
    BossObject = Writer.next_index + 1
    Writer.BeginObject(KBossClass, 1)
    WriteFolderName(Writer, Name, FeatureId, Flags=State.NodeFlags)
    Writer.u16(1)
    Writer.ReferenceObject(ProfileObject, KProfileClass)
    Writer.i32(0)
    WriteArcFeature(Writer, Generation, State.Feature, AllowRegenTime=True)
    Writer.raw(PackFields("<i3H", 0, 0, 0, 0))
    Writer.i32(1)
    Writer.u16(1)
    Writer.ReferenceObject(Atom.ObjectIndex, KAtomClass)
    Writer.i32(0)
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<5i", 1, Atom.AtomId, 3, 0, 1))
    return {
        "object_index": BossObject,
        "native_feature_id": FeatureId,
        "file_ref_object": FileObject,
    }
