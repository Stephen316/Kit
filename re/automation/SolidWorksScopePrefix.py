from functools import partial

from PairedCaptureIntake import require, sha256

from convert.adapters.solidworks.config import Presentation as presentation
from convert.adapters.solidworks.config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.config.OrdinaryMap import ReadEmptyRel, ReadRelEntry
from convert.adapters.solidworks.config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    KObjectRefKind,
    ReadTag,
)
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.ContourChain import ReadChainState
from convert.adapters.solidworks.resolved.FaceIdentity import KCapClass, ReadFaceHead
from convert.adapters.solidworks.resolved.NamedNode import ReadNamedNode
from convert.adapters.solidworks.resolved.OriginProfile import ReadOrigin
from convert.adapters.solidworks.resolved.ProfilePlane import ReadProfileRef
from convert.adapters.solidworks.resolved.ProfileSketch import ReadProfileBody
from convert.adapters.solidworks.resolved.RectanglePart import ResolveDatum
from convert.adapters.solidworks.resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.resolved.SavedFileRef import ReadFileRef
from convert.adapters.solidworks.resolved.SystemPrefix import ReadSysPrefix


def read_block_manager(cursor, pointer):
    start = cursor.Offset
    manager = pointer(KDefinitionKind, "moSketchBlockMgr_c")
    null = partial(pointer, KNullKind)
    null()
    state_offset = cursor.Offset
    concept = cursor.ReadInts("<iIii")
    require(concept == (1, 0x40000000, -1, 0), "unexpected scoped block concept")
    require(cursor.ReadText() == "" and cursor.ReadCount() == 0, "unexpected scoped block children")
    null()
    require(cursor.ReadInts("<Hi") == (0, 0), "unexpected scoped block return")
    ReadFeatBase(cursor.ReadValue, cursor.ReadPoint, null, cursor.ReadText)
    cursor.ReadValue("<16si")
    require(pointer(KObjectRefKind, "moSketchBlockMgr_c") == manager, "scoped block self-reference differs")
    require(cursor.ReadInts("<2i") == (0, 0), "unexpected scoped block tables")
    return {
        "start": start, "end": cursor.Offset, "object_index": manager,
        "concept_offset": state_offset, "concept_words": concept,
    }


def read_config_map(config):
    manager, count = ReadRelEntry(config, LoadPartLayouts(), (4,))
    body = manager.offset + ReadTag(config, manager.offset).size
    cursor = ArchiveCursor(config, body, manager.Counter, manager.Classes, manager.Objects)
    events = []
    pointer = partial(presentation.ReadModelTagMut, cursor, events)
    ReadEmptyRel(cursor)
    presentation.ReadSavedDetail(cursor, pointer)
    presentation.ReadEnvironment(cursor, pointer)
    presentation.ReadSavedViews(cursor, pointer)
    block = read_block_manager(cursor, pointer)
    pointer(KClassRefKind, "suObList")
    require(cursor.ReadInts("<H") == (1,), "expected one scoped annotation view")
    annotation = pointer(KDefinitionKind, "moAnnotationView_c")
    presentation.ReadAnnotView(cursor, pointer, ("*Top",))
    annotation_end = cursor.Offset
    presentation.ReadModelLists(cursor, pointer)
    presentation.ReadRegions(cursor)
    presentation.ReadExplManager(cursor, pointer)
    presentation.ReadPartReturn(cursor)
    require(cursor.Offset == len(config), "scoped configuration did not close at stream end")
    return cursor, {
        "sha256": sha256(config), "end": cursor.Offset, "next_map_index": cursor.NextIndex,
        "atom_count": count, "relation_manager_offset": manager.offset,
        "sketch_block_manager": block,
        "annotation": {"name": "*Top", "object_index": annotation, "end": annotation_end},
    }


def read_uncached_trim(cursor):
    start = cursor.Offset
    require(cursor.ReadInts("<2H") == (0, 4), "unsupported scoped profile flags")
    cursor.ReadNull()
    require(cursor.ReadInts("<2i") == (-1, 0), "unsupported scoped profile state")
    (state_word,) = cursor.ReadInts("<I")
    require(cursor.ReadInts("<H") == (1,), "unsupported scoped contour mode")
    cursor.ReadNull()
    require(cursor.ReadInts("<2Hi") == (0, 0, 0), "unexpected scoped trim cache")
    return {"start": start, "end": cursor.Offset, "state_word": state_word, "cached_surfaces": 0, "cached_segments": 0}


def read_boss_entry(cursor, profile, expected_name):
    start = cursor.Offset
    _, _, index = cursor.TakePointer(("moExtrusion_c",), KDefinitionKind, CompactOnly=True)
    cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    name, feature_id = ReadNamedNode(cursor, (0x40000140,))
    require(name == expected_name and cursor.ReadInts("<H") == (1,), "scoped boss does not own one profile")
    reference_offset = cursor.Offset
    _, _, target = cursor.TakePointer(("moProfileFeature_c",), KObjectRefKind, CompactOnly=True)
    require(target == profile.ObjectIndex, "scoped boss does not refer to the preceding typed sketch")
    require(cursor.ReadInts("<i") == (0,), "unexpected scoped boss node return")
    return {
        "name": name, "feature_id": feature_id, "object_index": index,
        "start": start, "end": cursor.Offset, "next_map_index": cursor.NextIndex,
        "profile_reference_offset": reference_offset, "profile_object_index": target,
    }


def read_first_cap(cursor, boss):
    ReadFeatBase(cursor.ReadValue, cursor.ReadPoint, cursor.ReadNull, cursor.ReadText)
    require(cursor.ReadInts("<i3H") == (0, 0, 0, 0), "unexpected scoped boss frame")
    require(cursor.ReadInts("<iH") == (1, 1), "expected one scoped boss transfer object")
    _, _, transfer = cursor.TakePointer(("moAtom_c",), KObjectRefKind, CompactOnly=True)
    require(cursor.ReadInts("<i") == (0,), "unexpected secondary scoped boss transfer")
    cursor.ReadNull()
    require(cursor.ReadInts("<5i") == (1, 101, 3, 0, 1), "unexpected scoped boss atom fields")
    require(cursor.ReadInts("<2H") == (1, 1), "expected one scoped body chooser")
    cursor.TakePointer(("moPerBodyChooserData_c",), KDefinitionKind, CompactOnly=True)
    require(cursor.ReadInts("<H") == (2,), "expected two scoped boss chooser caps")
    face, edges = ReadFaceHead(cursor, KDefinitionKind, 768)
    require(face["classifier"] == 0 and edges == 4, "unexpected first scoped cap")
    start = cursor.Offset
    _, _, cap = cursor.TakePointer((KCapClass,), KDefinitionKind, CompactOnly=True)
    cursor.ReadNull()
    feature_ref_offset = cursor.Offset
    _, _, feature_ref = cursor.TakePointer(("moFR_c",), KDefinitionKind, CompactOnly=True)
    file_ref = ReadFileRef(cursor)
    owner, clock_word, occurrence, selector = cursor.ReadInts("<iI2i")
    require((owner, occurrence, selector) == (boss["feature_id"], 0, 0), "scoped cap owner or selector differs")
    return {
        "start": start, "end": cursor.Offset, "object_index": cap, "feature_id": owner,
        "transfer_object_index": transfer, "feature_reference_offset": feature_ref_offset,
        "feature_reference_object": feature_ref, "file_reference": file_ref, "clock_word": clock_word,
    }


def read_scope_prefix(archive, resolved, spec, generation):
    config_map, config_report = read_config_map(archive.require("Contents/Config-0"))
    cursor = OpenResolved(resolved, config_map, 23)
    system = ReadSysPrefix(cursor)
    origin = ReadOrigin(cursor, generation)
    require(origin.Support.FeatureId == system.Planes[0].FeatureId, "scoped origin does not resolve the front plane")
    profile = ReadProfileBody(cursor, generation)
    producer = spec["bodies"]["A"]["producer"]
    require(profile.NameValue == producer + "Sketch", "scoped first profile differs from the recipe")
    edge_ids = tuple(line["native_id"] for line in profile.Geometry["lines"] if line["native_id"] >= 0)
    require(len(edge_ids) == len(set(edge_ids)) == 4, "scoped first profile does not have four distinct saved edges")
    ReadChainState(cursor, True, edge_ids)
    datum, _ = ResolveDatum(ReadProfileRef(cursor, generation), system.Planes)
    trim = read_uncached_trim(cursor)
    boss = read_boss_entry(cursor, profile, producer)
    return {
        "configuration": config_report, "resolved_list_count": 23,
        "first_profile": {
            "name": profile.NameValue, "feature_id": profile.FeatureId,
            "object_index": profile.ObjectIndex, "start": profile.Offset, "edge_ids": edge_ids,
            "datum": datum.NameValue, "datum_feature_id": datum.FeatureId, "trim": trim,
        },
        "first_boss": boss,
        "first_cap": read_first_cap(cursor, boss),
    }
