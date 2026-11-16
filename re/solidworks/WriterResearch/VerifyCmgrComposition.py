from dataclasses import replace
from hashlib import sha256
from struct import calcsize, unpack

from CmgrBaseHeader import CmgrBaseState, ReadCmgrHeader
from CmgrBossMass import BossMass, BossMassFields, ReadBossMass
from CmgrCollectionFront import ReadCmgrFront
from CmgrCollections import ReadCollections
from CmgrColorReadback import ReadColorSpan
from CmgrComposition import BuildCmgr, CmgrDocument, CmgrRectangularBoss
from CmgrExternal import ReadCmgrExt
from CmgrInherited import ReadCmgrFeature
from CmgrMass import KGeometryLayout, ReadEmptyMass
from CmgrOpening import ReadOpenFields
from CmgrPartEnd import ReadCmgrAliases, ReadCmgrPartEnd
from CmgrTail import ReadCmgrTail
from DefinitionTail import ReadPartDefinitionTail
from HeaderLogs import ReadHeaderLogs
from HeaderSelf import ReadHeaderSelf
from VerifyCmgrBoss import GEOMETRY_TOLERANCES, boss_bounds
from VerifyCmgrPart import read_base_return, read_linked_atoms
from VerifyCmgrVisual import read_visual_fields
from convert.adapters.solidworks.Config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.RootAtoms import AtomEnd
from convert.adapters.solidworks.Config.RootFields import ModelAtomStart
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    KObjectRefKind,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)
from convert.adapters.solidworks.Container.Cmgr import FeatureStamp, Stamp
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.BossEntry import BossOperation
from convert.adapters.solidworks.Resolved.RectanglePart import ReadRectPart


def read_boss_stamp(data: bytes, boss: BossOperation) -> FeatureStamp:
    ref_offset = boss["profile_ref_offset"]
    tag = ReadTag(data, ref_offset)
    RequireArch(
        (tag.kind, tag.wide), (KObjectRefKind, False), "CMgr boss profile reference"
    )
    cursor = ArchiveCursor(data, ref_offset + tag.size, 0, {}, {})
    RequireArch(cursor.ReadInts("<i"), (0,), "CMgr resolved boss node return")
    ReadFeatBase(cursor.ReadValue, cursor.ReadPoint, cursor.ReadNull, cursor.ReadText)
    # ReadFeatBase ends after the high/low FILETIME words and its trailing short and ints.
    cursor.Offset -= calcsize("<2IH2i")
    high, low = cursor.ReadInts("<2I")
    return FeatureStamp(boss["native_feature_id"], Stamp(high, low))


def read_boss_atom(config: bytes, tree_id: int) -> int:
    model, _ = ReadModelEntry(config, LoadPartLayouts())
    _, start, count = ModelAtomStart(config, model)
    tag = ReadTag(config, start)
    RequireArch(
        (count, tag.kind, tag.schema, tag.class_name, tag.wide),
        (1, KDefinitionKind, 1, "moAtom_c", False),
        "CMgr single owned configuration atom",
    )
    end = AtomEnd(config, start + tag.size)
    cursor = FieldCursor(config, end - calcsize("<13i"))
    atom_id, _, feature_id, repeated_id, *_ = cursor.ReadInts("<13i")
    RequireArch(
        (feature_id, repeated_id), (tree_id, tree_id), "CMgr atom's two feature IDs"
    )
    return atom_id


def read_rectangular_boss(
    archive: SldprtArchive, generation: int, measurement, body_stamp: int
) -> CmgrRectangularBoss | None:
    config = archive.require("Contents/Config-0")
    resolved = archive.require("Contents/Config-0-ResolvedFeatures")
    part = ReadRectPart(config, resolved, generation)
    count = measurement["body_count"]
    RequireArch(
        count, int(part.Boss is not None), "CMgr measured and resolved solid count"
    )
    if part.Boss is None:
        return None
    lower, upper = boss_bounds(part, measurement)
    definition = archive.require("Contents/Definition")
    density = ReadPartDefinitionTail(
        definition, len(definition) - calcsize("<id"), generation
    )
    feature = read_boss_stamp(resolved, part.Boss)
    atom = read_boss_atom(config, feature.tree_id)
    return CmgrRectangularBoss(atom, feature, body_stamp, lower, upper, density)


def compare_composed_mass(
    saved: BossMass, generated: bytes, start: int, generation: int
) -> tuple[float, ...]:
    cursor = FieldCursor(generated, start)
    new = ReadBossMass(cursor, generation, 1)
    deltas = tuple(
        abs(derived - native)
        for derived, native in zip(
            BossMassFields(new), BossMassFields(saved), strict=True
        )
    )
    RequireArch(
        all(
            delta <= limit
            for delta, limit in zip(deltas, GEOMETRY_TOLERANCES, strict=True)
        ),
        True,
        "CMgr composed single-boss geometry within measured tolerance",
    )
    return deltas


# the independent reader supplies typed manager state and the physical payload boundary
def read_cmgr_document(archive: SldprtArchive, generation: int, measurement):
    _, session_stamp, body_stamp = unpack("<3I", archive.require("ModelStamps"))
    header_cursor, header = ReadHeaderLogs(
        archive.require("Contents/Config-0-ModelHeader"), generation
    )
    RequireArch(session_stamp, header.UpdateStamp, "CMgr document update stamp owner")
    shared_file = ReadHeaderSelf(header_cursor, generation).File
    boss = read_rectangular_boss(archive, generation, measurement, body_stamp)
    atom_ids = (boss.AtomId,) if boss is not None else ()
    feature_stamps = (boss.Feature,) if boss is not None else ()
    count = len(atom_ids)

    stream = archive.require("Contents/CMgr")
    cursor, opening, slots = ReadOpenFields(stream, generation)
    visual = read_visual_fields(cursor)
    color, dspbr_start, checked = ReadColorSpan(stream, generation)
    RequireArch(
        (cursor.Offset, visual.SurfaceColor),
        (dspbr_start, color),
        "CMgr visual boundary",
    )
    part_time = ReadCmgrFeature(checked, generation)
    state = ReadCmgrHeader(checked, generation)
    RequireArch(
        state,
        CmgrBaseState(header.NextTreeId - 1, session_stamp, body_stamp if count else 0),
        "CMgr document allocator and configuration stamps",
    )
    mass_start = checked.Offset
    stored_mass = None
    if count:
        stored_mass = ReadBossMass(checked, generation, count)
    else:
        checked.Offset = ReadEmptyMass(stream, mass_start, generation, count)
    ReadCmgrFront(checked, generation, BodyCount=count, SaveMode=1)
    RequireArch(
        ReadCollections(checked, generation), atom_ids, "CMgr material atom ownership"
    )
    RequireArch(
        read_linked_atoms(checked, tuple(entry.tree_id for entry in feature_stamps)),
        atom_ids,
        "CMgr link atom ownership",
    )
    read_base_return(checked, atom_ids)
    RequireArch(
        ReadCmgrPartEnd(checked, Generation=generation, ConditionOne=False),
        atom_ids,
        "CMgr part atom ownership",
    )
    ReadCmgrAliases(checked, slots.PartObject)
    external = ReadCmgrExt(checked, generation)
    external_input = replace(shared_file, Flags=external.Flags)
    RequireArch(external_input == external, True, "CMgr shared ModelHeader file fields")
    RequireArch(
        ReadCmgrTail(checked, generation),
        feature_stamps,
        "CMgr resolved feature stamps",
    )

    document = CmgrDocument(
        opening,
        visual,
        part_time,
        header.NextTreeId,
        session_stamp,
        external_input,
        boss,
    )
    return document, checked, mass_start, stored_mass


# the geometry payload is the only part of the manager subject to physical tolerances
def compare_cmgr_bytes(saved, generated, mass_start, stored_mass, generation):
    RequireArch(len(generated), len(saved), "complete generated configuration manager")
    if stored_mass is None:
        RequireArch(generated, saved, "exact reconstructed sketch CMgr")
        return len(saved), ()
    geometry_end = mass_start + calcsize(KGeometryLayout)
    RequireArch(generated[:mass_start], saved[:mass_start], "CMgr before boss geometry")
    RequireArch(
        generated[geometry_end:], saved[geometry_end:], "CMgr after boss geometry"
    )
    deltas = compare_composed_mass(stored_mass, generated, mass_start, generation)
    return len(saved) - (geometry_end - mass_start), deltas


# Only discovery configurations with a sketch or a single rectangular boss take this proof.
def verify_cmgr_composition(
    archive: SldprtArchive, generation: int, measurement
) -> dict[str, object]:
    stream = archive.require("Contents/CMgr")
    document, checked, mass_start, stored_mass = read_cmgr_document(
        archive, generation, measurement
    )
    writer = BuildCmgr(generation, document)
    generated = writer.build()
    RequireArch(
        (len(generated), writer.next_index, writer.classes),
        (
            len(stream),
            checked.NextIndex,
            {name: index for index, name in checked.Classes.items()},
        ),
        "CMgr composed full stream size and live allocator",
    )

    exact_width, deltas = compare_cmgr_bytes(
        stream, generated, mass_start, stored_mass, generation
    )
    return {
        "source_sha256": sha256(stream).hexdigest(),
        "generated_sha256": sha256(generated).hexdigest(),
        "exact_bytes": exact_width,
        "geometry_deltas": deltas,
        "next_index": writer.next_index,
    }
