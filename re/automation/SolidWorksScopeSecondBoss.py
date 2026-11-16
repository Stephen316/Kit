from math import isclose

from PairedCaptureIntake import require

from convert.adapters.solidworks.config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.container.Archive import KClassRefKind, KDefinitionKind, KObjectRefKind
from convert.adapters.solidworks.resolved.BossChooser import CheckChoiceOwn, ReadChoiceTail
from convert.adapters.solidworks.resolved.BossDepth import ReadBossDepth
from convert.adapters.solidworks.resolved.BossEnd import ReadEndHead, ReadStartHead
from convert.adapters.solidworks.resolved.BossEntry import ReadBodyReturn, ReadOpNode
from convert.adapters.solidworks.resolved.ContourChain import ReadChain
from convert.adapters.solidworks.resolved.FaceIdentity import ReadFaceHead, ReadFaceReturn, ReadSurfaceId
from convert.adapters.solidworks.resolved.PlaneAtom import ReadAtomMaps
from convert.adapters.solidworks.resolved.ProfileEntry import ReadProfileHead
from convert.adapters.solidworks.resolved.ProfilePlane import ReadProfileRef
from convert.adapters.solidworks.resolved.ProfileSketch import ReadProfileBody
from convert.adapters.solidworks.resolved.RectanglePart import ResolveDatum


CAP_CLASS = "moEndFace3IntSurfIdRep_c"
EDGE_CLASS = "moFromSktEnt3IntSurfIdRep_c"


def read_uncached_trim(cursor, contour_mode=1):
    start = cursor.Offset
    require(cursor.ReadInts("<2H") == (0, 4), "unsupported scoped profile flags")
    cursor.ReadNull()
    require(cursor.ReadInts("<2i") == (-1, 0), "unsupported scoped profile state")
    (state_word,) = cursor.ReadInts("<I")
    require(cursor.ReadInts("<H") == (contour_mode,), "unsupported scoped contour mode")
    cursor.ReadNull()
    require(cursor.ReadInts("<2Hi") == (0, 0, 0), "unexpected scoped trim cache")
    return {"start": start, "end": cursor.Offset, "state_word": state_word, "cached_surfaces": 0, "cached_segments": 0}


def read_second_profile(cursor, generation, planes, producer):
    profile = ReadProfileBody(cursor, generation, ProfileKind=KClassRefKind, EnvironmentLead=5)
    require(profile.NameValue == producer + "Sketch", "unexpected second scoped profile name")
    sketch_end = cursor.Offset
    edge_ids = tuple(line["native_id"] for line in profile.Geometry["lines"] if line["native_id"] >= 0)
    require(len(set(edge_ids)) == len(edge_ids) == 4, "expected four second scoped sketch edges")
    require(cursor.ReadInts("<Ii") == (1, 1), "expected one second scoped contour chain")
    chain = ReadChain(cursor)
    require(sorted(chain["edge_ids"]) == sorted(edge_ids), "second scoped chain does not cover its edges")
    datum, _ = ResolveDatum(ReadProfileRef(cursor, generation), planes)
    require(datum.FeatureId == planes[0].FeatureId, "second scoped profile does not resolve the front plane")
    trim = read_uncached_trim(cursor, 3)
    return {
        "name": profile.NameValue, "feature_id": profile.FeatureId, "object_index": profile.ObjectIndex,
        "offset": profile.Offset, "sketch_object": profile.SketchIndex, "sketch_offset": profile.SketchOffset,
        "sketch_end": sketch_end, "edge_ids": edge_ids, "chain": chain,
        "datum": datum.NameValue, "datum_feature_id": datum.FeatureId, "trim": trim, "contour_mode": 3,
    }


def read_offset_cap(cursor, node, cap_kind, edge_kind, occurrence, classifier, edge_ids):
    face, count = ReadFaceHead(cursor, KClassRefKind, 768)
    require(face["classifier"] == classifier, "unexpected offset boss face classifier")
    primary = ReadSurfaceId(cursor, CAP_CLASS, cap_kind)
    require(
        cursor.ReadInts("<2i") == (0, 0) and primary["occurrence"] == occurrence,
        "unexpected offset boss cap selectors or occurrence",
    )
    edges = []
    for kind in [edge_kind] + [KClassRefKind] * (count - 1):
        edge = ReadSurfaceId(cursor, EDGE_CLASS, kind)
        require(cursor.ReadInts("<2i") == (-1, 0), "unexpected offset boss edge selectors")
        edges.append(edge)
    for surface in (primary, *edges):
        require(
            (surface["file_ref_object"], surface["feature_id"], surface["time_word"])
            == (node["file_ref_object"], node["native_feature_id"], primary["time_word"]),
            "offset boss chooser surface refers to a different source",
        )
    occurrences = [edge["occurrence"] for edge in edges]
    require(sorted(occurrences) == sorted(edge_ids), "offset boss chooser has different edge occurrences")
    ReadFaceReturn(cursor)
    return {
        **face, "end": cursor.Offset, "cap_object": primary["object_index"], "cap_occurrence": occurrence,
        "edge_objects": [edge["object_index"] for edge in edges], "edge_occurrences": occurrences,
    }, primary["time_word"]


def read_offset_alias(cursor, cap):
    face, count = ReadFaceHead(cursor, KClassRefKind, 768)
    require(face["classifier"] == 0, "unexpected offset boss alias classifier")
    _, _, cap_object = cursor.TakePointer((CAP_CLASS,), KObjectRefKind, CompactOnly=True)
    edge_objects = [cursor.TakePointer((EDGE_CLASS,), KObjectRefKind, CompactOnly=True)[2] for _ in range(count)]
    require(
        (cap_object, edge_objects) == (cap["cap_object"], cap["edge_objects"]),
        "offset boss chooser alias refers to different surfaces",
    )
    ReadFaceReturn(cursor)
    return {**face, "end": cursor.Offset, "cap_object": cap_object, "edge_objects": edge_objects}


def read_offset_choices(cursor, node, edge_ids):
    require(cursor.ReadInts("<2H") == (1, 1), "expected one offset boss chooser")
    _, _, primary = cursor.TakePointer(("moPerBodyChooserData_c",), KClassRefKind, CompactOnly=True)
    require(cursor.ReadInts("<H") == (2,), "expected two offset boss caps")
    first, first_clock = read_offset_cap(cursor, node, KDefinitionKind, KDefinitionKind, 0, 4977, edge_ids)
    second, second_clock = read_offset_cap(cursor, node, KClassRefKind, KClassRefKind, 1, 4891, edge_ids)
    bounds = ReadChoiceTail(cursor, KClassRefKind, ())
    CheckChoiceOwn(cursor, node, "moICE_c")
    require(cursor.ReadInts("<3H") == (1, 1, 0), "expected empty secondary offset boss chooser")
    CheckChoiceOwn(cursor, node, "moICE_c")
    require(cursor.ReadInts("<i2H") == (1, 1, 1), "expected one repeated offset boss chooser")
    _, _, repeat = cursor.TakePointer(("moPerBodyChooserData_c",), KClassRefKind, CompactOnly=True)
    require(cursor.ReadInts("<H") == (2,), "expected two repeated offset boss caps")
    aliases = [read_offset_alias(cursor, cap) for cap in (first, second)]
    repeated = ReadChoiceTail(cursor, KClassRefKind, ())
    require(repeated["centre_and_scale"] == bounds["centre_and_scale"], "different offset boss chooser centres")
    CheckChoiceOwn(cursor, node, "moICE_c")
    return {
        "primary_object": primary, "repeated_object": repeat, "caps": [first, second], "aliases": aliases,
        "centre": bounds, "repeated_centre_object": repeated["centre_object"], "end": cursor.Offset,
    }, [first_clock, second_clock]


def read_offset_bounds(cursor, node, edge_ids):
    ReadFeatBase(cursor.ReadValue, cursor.ReadPoint, cursor.ReadNull, cursor.ReadText)
    require(cursor.ReadInts("<i3H") == (0, 0, 0, 0), "unexpected offset boss framing")
    require(cursor.ReadInts("<iH") == (1, 1), "expected one offset boss transfer")
    _, _, transfer = cursor.TakePointer(("moAtom_c",), KObjectRefKind, CompactOnly=True)
    require(cursor.ReadInts("<i") == (0,), "unexpected secondary offset boss transfer")
    cursor.ReadNull()
    atoms = cursor.ReadInts("<5i")
    require(atoms == (1, 102, 3, 0, 1), "unexpected offset boss atom framing")
    choices, clocks = read_offset_choices(cursor, node, edge_ids)
    require(cursor.ReadInts("<H3i") == (0, 0, 0, 1), "unexpected offset boss partition")
    _, _, marker = cursor.TakePointer(("moPMarkRecord_c",), KClassRefKind, CompactOnly=True)
    (state,) = cursor.ReadInts("<i")
    ReadAtomMaps(cursor)
    ReadBodyReturn(cursor)
    return {
        "transfer_object": transfer, "atom_fields": atoms, "choices": choices,
        "partition_object": marker, "partition_state": state,
    }, clocks


def read_offset_extents(cursor, spec, centre):
    extent = ReadEndHead(cursor, KClassRefKind)
    require(extent["conditions"] == (0, 0), "second scoped boss is not blind")
    depth = ReadBossDepth(cursor, KClassRefKind, DisplayMode=200)
    start_spec = ReadStartHead(cursor, KClassRefKind, 0)
    (mode,) = cursor.ReadInts("<i")
    require(mode == 5, "unexpected offset boss start mode")
    offset = ReadBossDepth(cursor, KClassRefKind, DisplayMode=200)
    lead, token, tail = cursor.ReadValue("<i16si")
    require((lead, tail) == (1, 1), "unexpected offset start framing")
    require(cursor.ReadValue("<di") == (0, 0), "unexpected offset boss return")
    lower, upper = spec["bodies"]["B"]["bounds_mm"]
    depth_mm = depth["dimension"]["metres"] * 1000
    offset_mm = offset["dimension"]["metres"] * 1000
    expected = (upper[2] - lower[2], abs(lower[2]), *((a + b) / 2 for a, b in zip(lower, upper, strict=True)))
    observed = (depth_mm, offset_mm, *(value * 1000 for value in centre[:3]))
    require(
        all(isclose(a, b, rel_tol=0, abs_tol=spec["tolerances"]["length_mm_absolute"])
            for a, b in zip(observed, expected, strict=True)),
        "offset boss depth, offset or centre differs from the controls",
    )
    return {
        "blind_extent": extent, "depth_display": depth, "depth_mm": depth_mm,
        "start_spec_object": start_spec, "start_mode_word": mode, "start_display": offset, "start_offset_mm": offset_mm,
        "end": cursor.Offset, "next_map_index": cursor.NextIndex,
    }, token.hex()


def read_second_boss(cursor, spec, generation, planes, file_object):
    producer = spec["bodies"]["B"]["producer"]
    profile = read_second_profile(cursor, generation, planes, producer)
    node = ReadOpNode(cursor, "moICE_c", (0x40000140,), profile["object_index"], file_object)
    require(node["name"] == producer, "second scoped boss name differs from the recipe")
    bounds, clocks = read_offset_bounds(cursor, node, profile["edge_ids"])
    end, token = read_offset_extents(cursor, spec, bounds["choices"]["centre"]["centre_and_scale"])
    cut_offset = cursor.Offset
    _, _, cut_object = cursor.TakePointer(("moProfileFeature_c",), KClassRefKind, CompactOnly=True)
    cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    cut_name, cut_feature, _ = ReadProfileHead(cursor, (0x40000000, 0xC0000000))
    require(cut_name == spec["cut"]["sketch"], "second scoped boss did not close at the Cut profile")
    return {
        "second_profile": profile, "second_boss": node, "second_operation": {**bounds, **end},
        "cut_profile_entry": {
            "offset": cut_offset, "object_index": cut_object, "name": cut_name, "feature_id": cut_feature,
            "sketch_offset": cursor.Offset,
        },
        "second_archive_words": {"cap_clock_words": clocks, "start_token_hex": token},
    }
