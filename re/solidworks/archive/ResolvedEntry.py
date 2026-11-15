"""Replay the P04 resolved-list entry through the blind boss end-specification prefix."""

from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack_from
import sys

from FaceEvidence import WINDOWS
from SketchEvidence import (
    KApplicationBuild,
    KCaptureRev,
    KReceiptDigest,
    ReadPinned,
    ReadReceipts,
)

# the two licensed handoff and profile observations are bound to exact streams
CONTROLS = {
    "P04-solidworks-baseline-a.SLDPRT": {
        "config_sha256": "e40cdd1e562a9e501a0a29ac252745d5c5cac6a7265ef924ccef4f5d078b34ab",
        "handoff_sha256": "54f90a4fa10312c19bab9422e6a493daa96034187083b4a02203e087080c5bb9",
        "link_sha256": "5e41476686bc7c294795f9806a9136c78cf44377c0b65350d5c19b1158f4b5ae",
        "cut_start": 9417,
    },
    "P04-solidworks-plane-yz.SLDPRT": {
        "config_sha256": "72ceb3ef354feed23fd70e5de87f05a44090972941ff81abbb5a504609a0ad46",
        "handoff_sha256": "fd422752ee69e812b6cfc43c18ca2392f859c388a24b429b0ab41ed14d780423",
        "link_sha256": "ec2f13d1f6e2d79ea9a59f4368a51c10772e002060c3fde0c7173673584f50f6",
        "cut_start": 9487,
    },
}


# the annotations cabinet and ordinary named features share lightweight concept framing
def read_named_concept(cursor, expected_flags):
    from convert.adapters.solidworks.container.Archive import ReadString
    from SketchRoot import Require
    from SupportPlane import read_empty_label

    name, length = ReadString(cursor.blob, cursor.position)
    cursor.position += length
    node_state, flags, node_id, node_tail = cursor.read("<iIii")
    Require((node_state, node_tail), (0, 0), "ordinary typed node")
    Require(flags in expected_flags, True, "witnessed typed node flags")
    read_empty_label(cursor)
    Require(cursor.read("<i"), (0,), "empty lightweight child list")
    cursor.null()  # moVisualProperties_c
    return name, node_id


# ordinary features can proceed to their own fields after an empty resolved list
def read_named_feature(cursor, expected_flags=(0x40000000,)):
    from SketchRoot import Require
    from SupportPlane import read_feature_base

    name, node_id = read_named_concept(cursor, expected_flags)
    Require(cursor.read("<Hi"), (0, 0), "empty resolved node list and tail")
    read_feature_base(cursor)
    return name, node_id


# folder subclasses share a named feature base and keep their own guarded suffixes
def read_folder(cursor, type_name, suffix_format, suffix, null_children=0):
    from convert.adapters.solidworks.container.Archive import (
        KClassRefKind,
        KDefinitionKind,
    )
    from SketchRoot import Require

    offset = cursor.position
    object_index = cursor.pointer(KDefinitionKind, type_name)
    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, feature_id = read_named_feature(cursor)
    Require(cursor.read(suffix_format), suffix, f"guarded {type_name} suffix")
    for _ in range(null_children):
        cursor.null()
    return {
        "class": type_name,
        "name": name,
        "native_feature_id": feature_id,
        "object_index": object_index,
        "offset": offset,
        "cursor": cursor.position,
        "next_map_index": cursor.next_index,
    }


# the notes start and end tag use the same inherited folder framing
def read_notes_base(cursor):
    from convert.adapters.solidworks.container.Archive import KClassRefKind
    from SketchRoot import Require

    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, native_id = read_named_feature(cursor)
    Require(cursor.read("<2i"), (1, 0), "guarded notes folder base")
    return {"name": name, "native_feature_id": native_id}


# cabinet membership includes a backreference to the already allocated end tag
def read_detail_cabinet(cursor):
    from convert.adapters.solidworks.container.Archive import (
        KClassRefKind,
        KDefinitionKind,
        KObjectRefKind,
    )
    from SketchRoot import Require
    from SupportPlane import read_feature_base

    offset = cursor.position
    cabinet = cursor.pointer(KDefinitionKind, "moDetailCabinet_c")
    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, native_id = read_named_concept(cursor, (0x40000000,))
    Require(cursor.read("<H"), (2,), "two resolved cabinet members")

    notes_class = "moNotesAreaFtrFolder_c"
    notes = cursor.pointer(KDefinitionKind, notes_class)
    notes_fields = read_notes_base(cursor)
    end_tag = cursor.pointer(KClassRefKind, notes_class)
    end_fields = read_notes_base(cursor)
    Require(
        cursor.pointer(KObjectRefKind, notes_class),
        notes,
        "end tag points to notes owner",
    )
    Require(cursor.read("<4i"), (0, 0, 1, 1), "guarded end tag trailer")
    Require(cursor.read("<4i"), (1, 0, 1, 1), "guarded notes trailer")

    Require(
        cursor.pointer(KObjectRefKind, notes_class),
        end_tag,
        "second cabinet member is the same end tag",
    )
    Require(cursor.read("<i"), (0,), "guarded cabinet list trailer")
    read_feature_base(cursor)
    tail = bytes(12) + b"\xf0\x3f" + bytes(6) + b"\xf0\x3f" + bytes(10)
    Require(cursor.read("<32s"), (tail,), "guarded cabinet scalar tail")
    return {
        "class": "moDetailCabinet_c",
        "name": name,
        "native_feature_id": native_id,
        "object_index": cabinet,
        "offset": offset,
        "cursor": cursor.position,
        "next_map_index": cursor.next_index,
        "notes": {**notes_fields, "object_index": notes},
        "end_tag": {**end_fields, "object_index": end_tag},
    }


# the principal plane payload owns the stored world normal and display frame
def read_default_plane_data(cursor, pointer_kind):
    from FaceOccurrence import read_transform
    from SketchRoot import Require

    data = cursor.pointer(pointer_kind, "moDefaultRefPlnData_c")
    point = cursor.vector(3)
    normal = cursor.vector(3)
    transform = read_transform(cursor)
    cursor.vector(4)
    cursor.null()  # moCompEdge_c
    Require(cursor.read("<3iB"), (0, -4, -4, 0), "guarded default plane fields")
    cursor.vector(3)  # display root
    Require(cursor.read("<2iH"), (1, 0, 0), "guarded default plane scalar tail")
    for _ in range(3):
        cursor.null()  # facet reference, axis and sketch entity
    return {
        "object_index": data,
        "point_metres": point,
        "normal_world": normal,
        "transform": transform,
    }


# principal planes use the same model feature and atom as component reference planes
def read_principal_plane(cursor, pointer_kind):
    from convert.adapters.solidworks.container.Archive import KClassRefKind
    from SketchRoot import Require
    from SupportPlane import read_plane_atom, read_ref_geometry

    offset = cursor.position
    plane = cursor.pointer(pointer_kind, "moRefPlane_c")
    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, feature_id = read_named_feature(cursor, expected_flags=(0xC0000000,))
    Require(cursor.read("<i"), (0,), "guarded principal model feature")
    read_plane_atom(cursor)
    read_ref_geometry(cursor, expected_mode=5)
    data = read_default_plane_data(cursor, pointer_kind)
    return {
        "name": name,
        "native_feature_id": feature_id,
        "offset": offset,
        "cursor": cursor.position,
        "object_index": plane,
        "next_map_index": cursor.next_index,
        "plane_data": data,
    }


# origin and user profiles both need the same framing for the earlier null pointer
def read_profile_body_prefix(cursor, expected_flags):
    from SketchRoot import Require

    name, feature_id = read_named_feature(cursor, expected_flags)
    cursor.read("<i")  # moModelFeature_c
    Require(cursor.read("<i"), (0,), "guarded scalar before the early profile pointer")
    early_pointer = cursor.position
    cursor.null()
    Require(cursor.read("<i"), (0,), "guarded scalar after the early profile pointer")
    return name, feature_id, early_pointer


# the origin materializes a resolved only sketch through the retained configuration class
def read_origin_entry(cursor):
    from convert.adapters.solidworks.container.Archive import (
        KClassRefKind,
        KDefinitionKind,
    )
    from OriginTail import read_feature_tail, read_presentation
    from SketchRoot import Require

    offset = cursor.position
    origin = cursor.pointer(KDefinitionKind, "moOriginProfileFeature_c")
    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, feature_id, _ = read_profile_body_prefix(cursor, (0xC0000000,))
    Require((name, feature_id), ("Origin", 5), "typed origin profile")
    sketch_offset = cursor.position
    sketch_kind = (
        KClassRefKind if "sgSketch" in cursor.classes.values() else KDefinitionKind
    )
    sketch = cursor.pointer(sketch_kind, "sgSketch")
    geometry = read_origin_geometry(cursor, sketch_offset)
    presentation = read_presentation(cursor)
    tail = read_feature_tail(cursor)
    return {
        "name": name,
        "native_feature_id": feature_id,
        "offset": offset,
        "object_index": origin,
        "sketch_offset": sketch_offset,
        "sketch_object": sketch,
        "geometry": geometry,
        "presentation": presentation,
        **tail,
        "end": cursor.position,
        "next_map_index": cursor.next_index,
    }


# the origin relation refers to a point handle within the sole origin point
def read_origin_geometry(cursor, sketch_offset):
    from types import SimpleNamespace

    from SketchCursor import SketchCursor
    from SketchGeom import ReadDims, ReadPointItem
    from SketchRoot import Require

    entry = SimpleNamespace(
        offset=sketch_offset,
        Counter=cursor.next_index,
        Classes=cursor.classes,
        Objects=cursor.objects,
    )
    sketch = SketchCursor(cursor.blob, entry, None)
    body = sketch.Offset
    Require(sketch.ReadCount(), 1, "one origin point")
    _, _, point = ReadPointItem(sketch)
    Require(point, (0, 0), "origin point coordinates")
    Require(sketch.ReadCount(), 0, "empty origin lines")
    ReadDims(sketch)
    Require(sketch.Dimensions, [], "empty origin value dimensions")
    Require(sketch.ReadValue("<3H"), (0, 0, 1), "one origin member relation")
    _, _, type_code = sketch.ReadDimBase(None)
    Require(type_code, 17, "witnessed origin relation type")
    Require(sketch.ReadValue("<2H"), (65534, 0), "guarded origin relation fields")
    handle = sketch.ReadObject("sgPointHandle")
    Require(
        sketch.Handles[handle], (0, -1, 0), "relation targets the local origin point"
    )
    cursor.position = sketch.Offset
    cursor.next_index = sketch.NextIndex
    return {
        "body": body,
        "end": cursor.position,
        "point_metres": point,
        "point_relation_type": type_code,
        "point_handle_object": handle,
    }


# sequential profile links must use an existing configuration sketch allocation
def read_profile_link(cursor, pointer_kind):
    from convert.adapters.solidworks.container.Archive import (
        KClassRefKind,
        KDefinitionKind,
        KObjectRefKind,
        ReadTag,
    )

    start = cursor.position
    class_index = (
        cursor.next_index
        if pointer_kind == KDefinitionKind
        else ReadTag(cursor.blob, start).index
    )
    object_index = cursor.pointer(pointer_kind, "moProfileFeature_c")
    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, feature_id, early_pointer = read_profile_body_prefix(
        cursor, (0x40000000, 0xC0000000)
    )
    sketch_offset = cursor.position
    sketch = cursor.pointer(KObjectRefKind, "sgSketch")
    return {
        "name": name,
        "native_feature_id": feature_id,
        "profile_offset": start,
        "profile_class": class_index,
        "profile_object": object_index,
        "early_profile_pointer": early_pointer,
        "sketch_offset": sketch_offset,
        "sketch_object": sketch,
    }


# an extrusion node must select the profile already allocated by this walk
def read_operation_node(cursor, class_name, flags, expected_profile, file_reference):
    from convert.adapters.solidworks.container.Archive import (
        KClassRefKind,
        KDefinitionKind,
        KObjectRefKind,
    )
    from SketchRoot import Require

    start = cursor.position
    index = cursor.pointer(KDefinitionKind, class_name)
    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, feature_id = read_named_concept(cursor, flags)
    Require(cursor.read("<H"), (1,), "one resolved operation profile")
    profile = cursor.pointer(KObjectRefKind, "moProfileFeature_c")
    Require(
        profile,
        expected_profile["profile_object"],
        "operation owns the reached profile",
    )
    Require(cursor.read("<i"), (0,), "guarded operation node trailer")
    return {
        "offset": start,
        "object_index": index,
        "name": name,
        "native_feature_id": feature_id,
        "profile_object": profile,
        "file_ref_object": file_reference,
    }


# the boss selects the rectangle profile and the file allocated by its contour
def read_boss_entry(cursor, rectangle, file_reference, *, directions=(0,)):
    from BossPrefix import read_boss_prefix

    boss = read_operation_node(
        cursor,
        "moExtrusion_c",
        (0x40000140, 0xC0000140),
        rectangle,
        file_reference["object_index"],
    )
    return read_boss_prefix(cursor, boss, directions=directions)


# folder suffixes are confined to the ordinary bodies at the start of these captures
def read_resolved_prelude(blob, config_map, expected_count):
    from convert.adapters.solidworks.container.Archive import (
        KClassRefKind,
        KDefinitionKind,
        KObjectRefKind,
    )
    from FaceOccurrence import FaceCursor
    from SketchRoot import Require

    base, count = unpack_from("<iH", blob)
    Require(base, config_map.NextIndex, "derived configuration map counter")
    Require(count, expected_count, "witnessed short resolved list")
    cursor = FaceCursor(
        blob,
        6,
        config_map.NextIndex,
        config_map.Classes.copy(),
        config_map.Objects.copy(),
    )
    folders = [
        read_folder(cursor, "moCommentsFolder_c", "<2i", (0, 0)),
        read_folder(cursor, "moFavoriteFolder_c", "<4i", (1, 0, 0, 1)),
        read_folder(cursor, "moHistoryFolder_c", "<2iH", (1, 0, 0)),
        read_folder(
            cursor,
            "moSelectionSetFolder_c",
            "<2i6s",
            (1, 0, b"\x00\x00\x01\x00\x00\x00"),
        ),
        read_folder(cursor, "moSensorFolder_c", "<2i", (1, 0)),
        read_folder(cursor, "moDocsFolder_c", "<2i", (1, 0)),
        read_detail_cabinet(cursor),
        read_folder(
            cursor, "moSurfaceBodyFolder_c", "<4i", (1, 0, 0, 0), null_children=2
        ),
        read_folder(
            cursor, "moSolidBodyFolder_c", "<4i", (1, 0, 0, 0), null_children=2
        ),
    ]
    alias_start = cursor.position
    environment = cursor.pointer(KObjectRefKind, "moEnvFolder_c")
    folders.extend(
        [
            read_folder(cursor, "moInkMarkupFolder_c", "<2i", (1, 0)),
            read_folder(cursor, "moEqnFolder_c", "<2i", (1, 0)),
            read_folder(
                cursor,
                "moMaterialFolder_c",
                "<2i8s",
                (1, 0, b"\xff\xfe\xff\x00\x00\x00\x00\x80"),
            ),
        ]
    )
    planes = [read_principal_plane(cursor, KDefinitionKind)]
    planes.extend(read_principal_plane(cursor, KClassRefKind) for _ in range(2))
    Require(
        [
            (
                item["name"],
                item["native_feature_id"],
                item["plane_data"]["normal_world"],
            )
            for item in planes
        ],
        [
            ("Front Plane", 2, (0, 0, 1)),
            ("Top Plane", 3, (0, 1, 0)),
            ("Right Plane", 4, (1, 0, 0)),
        ],
        "guarded principal plane identities and orientation",
    )
    origin = read_origin_entry(cursor)
    front, *_ = planes
    Require(
        origin["support"]["native_feature_id"],
        front["native_feature_id"],
        "origin support resolves the saved front plane",
    )
    origin["support"]["plane_object"] = front["object_index"]
    return cursor, {
        "list_count": count,
        "prior_map_index": base,
        "folders": folders,
        "environment_alias": {"offset": alias_start, "object_index": environment},
        "principal_planes": planes,
        "origin": origin,
    }


# P04 continues from the ordinary document prelude through the cut's dependencies
def read_list_prefix(
    blob, config_map, through_cut=False, through_support=False, through_operation=False
):
    from convert.adapters.solidworks.container.Archive import (
        KClassRefKind,
        KDefinitionKind,
    )
    from RectangleTail import read_rectangle_tail
    from SketchRoot import Require

    cursor, prelude = read_resolved_prelude(blob, config_map, 21)
    rectangle = read_profile_link(cursor, KDefinitionKind)
    planes = prelude["principal_planes"]
    rectangle_tail = read_rectangle_tail(cursor, rectangle, planes)
    boss = read_boss_entry(
        cursor, rectangle, rectangle_tail["trim_surface"]["file_reference"]
    )
    report = {
        **prelude,
        "rectangle_link": rectangle,
        "rectangle": rectangle_tail,
        "boss": boss,
        "next_class": "moDisplayDistanceDim_c",
        "next_offset": cursor.position,
        "next_map_index": cursor.next_index,
    }
    if through_cut or through_support or through_operation:
        from BossPrefix import read_boss_close

        boss.update(read_boss_close(cursor))
        cut = read_profile_link(cursor, KClassRefKind)
        Require(
            cut["profile_class"], rectangle["profile_class"], "shared profile class"
        )
        Require(
            cut["sketch_object"] != rectangle["sketch_object"],
            True,
            "distinct sketches",
        )
        del report["next_class"]
        report.update(
            cut_link=cut,
            stopped_in="moProfileFeature_c",
            next_offset=cursor.position,
            next_map_index=cursor.next_index,
        )
    if through_support or through_operation:
        from CutSupport import read_cut_support

        result = read_cut_support(cursor, report["cut_link"], boss)
        report.update(
            cut_support=result,
            next_offset=cursor.position,
            next_map_index=cursor.next_index,
        )
    if through_operation:
        from CutOperation import read_cut_operation
        from CutProfileTail import read_cut_profile_tail

        cut = report["cut_link"]
        tail = read_cut_profile_tail(cursor, cut, boss)
        node = read_operation_node(
            cursor, "moICE_c", (0x400201CA, 0xC00201CA), cut, boss["file_ref_object"]
        )
        operation = read_cut_operation(cursor, node, boss)
        del report["stopped_in"]
        report.update(
            cut_profile=tail,
            cut_operation=operation,
            list_complete=True,
            next_offset=cursor.position,
            next_map_index=cursor.next_index,
        )
    return report


# fixed witness anchors provide evidence before the full resolved list is available
def read_profile(blob, config_map, start, reference, reference_class, target):
    from convert.adapters.solidworks.container.Archive import (
        KClassRefKind,
        KDefinitionKind,
        KObjectRefKind,
        ReadTag,
    )
    from FaceOccurrence import FaceCursor
    from SketchRoot import Require

    tag = ReadTag(blob, start)
    if reference_class:
        Require(
            (tag.kind, tag.index),
            (KClassRefKind, reference_class),
            "existing profile class",
        )
    else:
        Require(
            (tag.kind, tag.schema, tag.class_name),
            (KDefinitionKind, 1, "moProfileFeature_c"),
            "typed profile definition",
        )
    name_tag = ReadTag(blob, start + tag.size)
    Require(
        (name_tag.kind, config_map.Classes.get(name_tag.index)),
        (KClassRefKind, "moNodeName_c"),
        "typed profile name in the configuration map",
    )
    cursor = FaceCursor(
        blob[: reference + 2],
        start + tag.size + name_tag.size,
        config_map.NextIndex,
        config_map.Classes,
        config_map.Objects,
    )
    name, feature_id, early_pointer = read_profile_body_prefix(cursor, (0x40000000,))
    Require(cursor.position, reference, "exact recorded sketch slot boundary")
    object_index = cursor.pointer(KObjectRefKind, "sgSketch")
    Require(object_index, target, "witnessed sketch object")
    return {
        "name": name,
        "native_feature_id": feature_id,
        "profile_offset": start,
        "early_profile_pointer": early_pointer,
        "sketch_offset": reference,
        "sketch_object": object_index,
    }


# native offsets corroborate reached links only on the two independently traced inputs
def compare_profile_witness(name, resolved, config_map, report, control):
    from CutSupport import check_cut_witness
    from SketchRoot import Require

    resolved_pin = WINDOWS[name]
    Require(
        (report["config_sha256"], report["resolved_sha256"]),
        (control["config_sha256"], resolved_pin["sha256"]),
        "pinned configuration and resolved streams",
    )
    profiles = [
        read_profile(resolved, config_map, 5525, 5742, None, 155),
        read_profile(
            resolved,
            config_map,
            control["cut_start"],
            resolved_pin["sketch_reference"],
            341,
            74,
        ),
    ]
    Require(
        [(item["name"], item["native_feature_id"]) for item in profiles],
        [("RectangleSketch", 26), ("CutSketch", 35)],
        "licensed profile names and identities",
    )
    rectangle = report["list_prefix"]["rectangle_link"]
    Require(
        {field: rectangle[field] for field in profiles[0]},
        profiles[0],
        "reached rectangle agrees with licensed profile",
    )
    cut = report["list_prefix"].get("cut_link")
    if cut is not None:
        Require(
            {field: cut[field] for field in profiles[1]},
            profiles[1],
            "reached cut agrees with licensed profile",
        )
    surface = report["list_prefix"]["rectangle"]["trim_surface"]
    Require(
        (surface["feature_ref_class"], surface["file_reference"]["object_index"]),
        (350, 353),
        "reached file reference agrees with licensed map",
    )
    boss = report["list_prefix"]["boss"]
    positive = boss["choosers"]["caps"][1]
    primary = positive["primary"]
    Require(
        (primary["feature_id"], primary["time_word"], primary["occurrence"]),
        (34, resolved_pin["time_word"], 1),
        "reached boss cap agrees with licensed cut support",
    )
    Require(
        [edge["occurrence"] for edge in positive["edges"]],
        resolved_pin["ordered_edges"],
        "reached boss cap has the licensed ordered boundaries",
    )
    cut_support = report["list_prefix"].get("cut_support")
    if cut_support is not None:
        check_cut_witness(cut_support, resolved_pin)
    report.update(
        native_handoff_witness_sha256=control["handoff_sha256"],
        native_profile_witness_sha256=control["link_sha256"],
        native_map_witness_sha256=resolved_pin["map_witness_sha256"],
        separately_witnessed_profiles=profiles,
    )


# exact blob pinning binds every sequential replay to its measured discovery case
def read_capture(
    root,
    asset,
    measured,
    through_cut=False,
    through_support=False,
    through_operation=False,
):
    from ConfigMap import ReadConfigMap
    from convert.adapters.solidworks.container.Archive import ContainerMo
    from convert.adapters.solidworks.container.Container import SldprtArchive
    from SketchRoot import KGeneration, Require

    name = asset["file"]
    native = ReadPinned(root, name)
    digest = sha256(native).hexdigest()
    Require((digest, len(native)), (asset["sha256"], asset["size_bytes"]), name)
    container = SldprtArchive.from_bytes(native, name)
    Require(ContainerMo(container.streams), KGeneration, "model generation")
    config = container.require("Contents/Config-0")
    resolved = container.require("Contents/Config-0-ResolvedFeatures")
    config_map, _ = ReadConfigMap(config, KApplicationBuild)
    prefix = read_list_prefix(
        resolved, config_map, through_cut, through_support, through_operation
    )
    profiles = [
        feature["name"]
        for feature in measured["feature_tree"]
        if feature["type"] == "ProfileFeature"
    ]
    rectangle = prefix["rectangle_link"]
    Require(profiles[:1], [rectangle["name"]], "first measured user profile")
    sketches = [
        item for item in measured["sketches"] if item["name"] == rectangle["name"]
    ]
    Require(len(sketches), 1, "one measured rectangle sketch")
    support = prefix["rectangle"]["support"]
    Require(
        support["plane_name"], sketches[0]["support_name"], "measured rectangle support"
    )
    transform = support["transform"]
    basis = transform["basis"] or (1, 0, 0, 0, 1, 0, 0, 0, 1)
    Require(
        (*basis, *transform["translation_scale"]),
        tuple(sketches[0]["model_to_sketch_transform"][:13]),
        "measured rectangle placement",
    )
    boss = prefix["boss"]
    measured_bosses = [
        feature
        for feature in measured["feature_tree"]
        if (feature["type"], feature["name"]) == ("Extrusion", boss["name"])
    ]
    Require(len(measured_bosses), 1, "one independently measured boss")
    spec = boss["end_specification"]
    measured_boss = measured_bosses[0]
    operation = measured_boss["operation"]
    Require(
        (spec["single_end"] == 0, spec["direction"] != 0, spec["conditions"][0]),
        (
            operation["both_directions"],
            operation["reverse_direction"],
            operation["end_condition"],
        ),
        "measured boss direction and termination",
    )
    if through_cut or through_support or through_operation:
        cut = prefix["cut_link"]
        Require(profiles[1:2], [cut["name"]], "second measured user profile")
        depth = boss["depth_display"]["dimension"]
        Require(depth["metres"], operation["depth_m"], "measured boss depth")
        dimensions = [
            item["system_value"]
            for item in measured_boss["dimensions"]
            if item["name"] == depth["parameter_name"]
        ]
        Require(dimensions, [depth["metres"]], "measured named boss depth dimension")
    if through_support or through_operation:
        from CutSupport import check_cut_normal

        cut = prefix["cut_link"]
        cuts = [item for item in measured["sketches"] if item["name"] == cut["name"]]
        Require(len(cuts), 1, "one measured cut sketch")
        check_cut_normal(prefix["cut_support"], cuts[0])
    if through_operation:
        from CutOperation import check_cut_operation

        check_cut_operation(prefix, measured, cuts[0])
    report = {
        "file": name,
        "native_sha256": digest,
        "config_sha256": sha256(config).hexdigest(),
        "resolved_sha256": sha256(resolved).hexdigest(),
        "list_prefix": prefix,
    }
    if name in CONTROLS:
        compare_profile_witness(name, resolved, config_map, report, CONTROLS[name])
    return report


# the report preserves the distinct sources of entry and profile provenance
def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--through-cut", action="store_true", help="walk to the CutSketch link"
    )
    parser.add_argument(
        "--through-support",
        action="store_true",
        help="walk through the CutSketch support",
    )
    parser.add_argument(
        "--through-operation",
        action="store_true",
        help="walk through the cut operation to the resolved list footer",
    )
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "src"))
    receipt, measured = ReadReceipts(root)
    evidence = {
        "scope": "p04_resolved_entry_research",
        "capture_revision": KCaptureRev,
        "capture_receipt_sha256": KReceiptDigest,
        "application_build": KApplicationBuild,
        "captures": [
            read_capture(
                root,
                asset,
                measured[asset["file"]],
                arguments.through_cut,
                arguments.through_support,
                arguments.through_operation,
            )
            for asset in receipt["native_files"]
        ],
    }
    output = json.dumps(evidence, sort_keys=True, indent=2, allow_nan=False)
    sys.stdout.buffer.write((output + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
