from math import isclose

from PairedCaptureIntake import require

from convert.adapters.solidworks.Config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind, KObjectRefKind
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPart
from convert.adapters.solidworks.Resolved.BossEntry import ReadOpNode
from convert.adapters.solidworks.Resolved.FaceIdentity import (
    KCapClass, KEdgeClass, ReadFaceHead, ReadFaceReturn, ReadSurfaceId, SurfaceKey,
)
from convert.adapters.solidworks.Resolved.Cut.CutChooser import KCutClass
from convert.adapters.solidworks.Resolved.Cut.CutProfileBody import ReadCutBody
from convert.adapters.solidworks.Resolved.Support.FaceFrame import ReadFacePose
from convert.adapters.solidworks.Resolved.Support.SupportPlane import ReadFaceSupport
from convert.adapters.solidworks.Sketch.InlineSketch import ParseInlineMut
from SolidWorksScopeSecondBoss import CAP_CLASS, EDGE_CLASS
from SolidWorksScopeTerminal import read_scope_terminal


def read_cut_sketch(cursor, generation, profile, spec):
    start = cursor.Offset
    _, _, sketch_object = cursor.TakePointer(("sgSketch",), KClassRefKind, CompactOnly=True)
    inline = ParseInlineMut(cursor, start, sketch_object, generation, EnvironmentLead=5)
    sketch_end = cursor.Offset
    points = inline.Geometry["points_metres"]
    lower, upper = spec["cut"]["profile_bounds_mm"]
    axes = tuple(zip(*points, strict=True))
    bounds_mm = tuple(tuple(bound(axis) * 1000 for axis in axes) for bound in (min, max))
    require(
        all(isclose(found, expected, rel_tol=0, abs_tol=spec["tolerances"]["length_mm_absolute"])
            for actual, recipe in zip(bounds_mm, (lower, upper), strict=True)
            for found, expected in zip(actual, recipe[:2], strict=True)),
        "scoped Cut sketch bounds differ from the recipe",
    )
    body = ReadCutBody(cursor, sketch_object)
    return {
        "profile_object": profile["object_index"], "sketch_object": sketch_object, "sketch_end": sketch_end,
        "bounds_mm": bounds_mm, "chain": body["chain"], "kernel_packet": body["kernel_packet"],
    }, body["edge_references"]


def read_cut_support(cursor, generation, spec, first_cap, first_choosers, projections):
    support = ReadFaceSupport(cursor, generation, 0)
    face = support["face"]
    plane = face["plane"]
    occurrence = face["component"]["occurrence"]
    file_object = first_cap["file_reference"]["object_index"]
    owner = (file_object, first_cap["feature_id"], first_cap["clock_word"])
    sides = first_choosers["second_cap_edge_occurrences"]
    require(
        SurfaceKey(occurrence["primary"]) == (*owner, 1)
        and [SurfaceKey(row) for row in occurrence["ordered_edges"]] == [(*owner, side) for side in sides],
        "scoped Cut support does not bind the first boss's other cap and ordered sides",
    )
    require(
        [edge["boundary_occurrences"][0] for edge in projections] == sides
        and all(SurfaceKey(edge["primary"]) == (*owner, 1)
                and len(set(edge["boundary_occurrences"])) == 3
                and set(edge["boundary_occurrences"]) <= set(sides) for edge in projections),
        "scoped Cut projected boundaries do not bind the first boss cap",
    )
    require(
        plane["normal_world"] == tuple(-value for value in spec["cut"]["direction_world"])
        and isclose(plane["root_metres"][2] * 1000, spec["cut"]["profile_bounds_mm"][0][2],
                    rel_tol=0, abs_tol=spec["tolerances"]["length_mm_absolute"]),
        "scoped Cut cap plane differs from the recipe",
    )
    placement = ReadFacePose(cursor)
    require(placement == plane["transform"], "scoped Cut placement differs from its saved face frame")
    require(cursor.ReadInts("<H") == (1,), "expected scoped Cut auxiliary placement")
    auxiliary = ReadFacePose(cursor)
    require(auxiliary == {"basis": None, "translation_scale": (0, 0, 0, 1)}, "unexpected scoped Cut auxiliary placement")
    require(cursor.ReadInts("<H") == (4,), "unexpected scoped Cut cache flags")
    cursor.ReadNull()
    first, second, state, mode = cursor.ReadInts("<2iIH")
    require((first, second, mode) == (-1, 0, 11), "unexpected scoped Cut cache framing")
    cursor.ReadNull()
    require(cursor.ReadInts("<2Hi") == (0, 0, 0), "unexpected scoped Cut cached surfaces or segments")
    return {
        "support_object": support["support_object"], "face_object": occurrence["object_index"],
        "support_offset": support["offset"], "support_end": face["support_end"], "cap_occurrence": 1,
        "feature_id": first_cap["feature_id"], "file_object": file_object, "plane": plane, "placement": placement,
        "boundary_occurrences": [row["boundary_occurrences"] for row in projections],
        "contour_mode": mode, "contour_state": state, "cached_surfaces": 0, "cached_segments": 0,
        "end": cursor.Offset, "next_map_index": cursor.NextIndex,
    }


def read_typed_scope_body(cursor, generation, kind, owner, classes):
    start = cursor.Offset
    _, _, body = cursor.TakePointer(("moCompSolidBody_c",), kind, CompactOnly=True)
    unit, part = ReadLocalPart(cursor, generation)
    face, count = ReadFaceHead(cursor, KClassRefKind, 512)
    cap_class, edge_class = classes
    surfaces = []
    for class_name in (edge_class, cap_class, edge_class, cap_class, edge_class):
        surface = ReadSurfaceId(cursor, class_name, IsCap=class_name == KCapClass)
        if class_name == CAP_CLASS:
            require(cursor.ReadInts("<2i") == (0, 0), "unexpected scoped offset cap selectors")
        if class_name == EDGE_CLASS:
            require(cursor.ReadInts("<2i") == (-1, 0), "unexpected scoped offset side selectors")
        require(SurfaceKey(surface)[:2] == owner, "scoped Cut face refers to a different boss or file")
        surfaces.append(surface)
    require(
        len(surfaces) == count + 1
        and [row["occurrence"] for row in surfaces] == [4, 0, 1, 1, 3]
        and len({row["time_word"] for row in surfaces}) == 1,
        "unexpected scoped Cut surface identities",
    )
    ReadFaceReturn(cursor)
    present, body_id, feature, atom, face_node = cursor.ReadInts("<5i")
    require(present == 1 and feature == owner[1], "scoped Cut result differs from its face owner")
    return {
        "offset": start, "end": cursor.Offset, "object_index": body, "body_id": body_id,
        "feature_id": feature, "recent_atom_id": atom, "face_node_id": face_node,
        "unit_component": unit, "part_object": part, "face": face,
        "surface_objects": [row["object_index"] for row in surfaces],
    }


def read_typed_scope(cursor, generation, first_cap, second_boss, second_operation):
    ReadFeatBase(cursor.ReadValue, cursor.ReadPoint, cursor.ReadNull, cursor.ReadText)
    require(cursor.ReadInts("<i3H") == (0, 0, 0, 0), "unexpected scoped Cut framing")
    transfers = []
    for _ in range(2):
        require(cursor.ReadInts("<iH") == (1, 2), "expected two scoped Cut transfer references")
        transfers.append([cursor.TakePointer(("moAtom_c",), KObjectRefKind, CompactOnly=True)[2] for _ in range(2)])
    require(
        set(transfers[1]) == {first_cap["transfer_object_index"], second_operation["transfer_object"]}
        and len(set(transfers[0] + transfers[1])) == 4,
        "scoped Cut parent array is not the two reached boss transfers",
    )
    cursor.ReadNull()
    count, a, b, atom_mode = cursor.ReadInts("<4i")
    require((count, atom_mode) == (2, 3) and 0 < a < b, "unexpected scoped Cut atom envelope")
    array_offset = cursor.Offset
    require(cursor.ReadInts("<iH") == (1, 2), "unexpected scoped Cut body array envelope")
    file_object = first_cap["file_reference"]["object_index"]
    first = read_typed_scope_body(cursor, generation, KDefinitionKind, (file_object, first_cap["feature_id"]), (KCapClass, KEdgeClass))
    second = read_typed_scope_body(cursor, generation, KClassRefKind, (file_object, second_boss["native_feature_id"]), (CAP_CLASS, EDGE_CLASS))
    require(
        [first["recent_atom_id"], second["recent_atom_id"]] == [a, b]
        and [first["body_id"], second["body_id"]] == [101, second_operation["atom_fields"][1]],
        "scoped Cut body and atom identities differ from the reached bosses",
    )
    scope_word_offset = cursor.Offset
    require(cursor.ReadInts("<i2H") == (1, 1, 2), "unexpected scoped Cut word or chooser lead")
    return {
        "transfers": transfers, "array_offset": array_offset, "bodies": [first, second],
        "scope_word_offset": scope_word_offset, "scope_word": 1, "end": cursor.Offset,
        "next_map_index": cursor.NextIndex,
    }


def read_scoped_cut(cursor, spec, generation, prefix, first_cap, first_choosers):
    profile = prefix["cut_profile_entry"]
    sketch, edges = read_cut_sketch(cursor, generation, profile, spec)
    support = read_cut_support(cursor, generation, spec, first_cap, first_choosers, edges)
    node = ReadOpNode(cursor, KCutClass, (0x400201CA,), profile["object_index"], support["file_object"], KindValue=KClassRefKind)
    require(node["name"] == spec["cut"]["feature"], "scoped Cut node differs from the recipe")
    scope = read_typed_scope(cursor, generation, first_cap, prefix["second_boss"], prefix["second_operation"])
    recording = {"cut_sketch": sketch, "cut_support": support, "cut_node": node, "cut_scope": scope}
    terminal = read_scope_terminal(cursor, recording, first_cap, first_choosers, prefix)
    return {**recording, "cut_terminal": terminal}
