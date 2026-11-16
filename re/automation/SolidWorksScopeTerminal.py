import struct

from PairedCaptureIntake import require

from convert.adapters.solidworks.Container.Archive import KClassRefKind, ReadTag
from convert.adapters.solidworks.Resolved.BossChooser import CheckChoiceOwn, ReadChoiceTail
from convert.adapters.solidworks.Resolved.BossEntry import ReadBodyReturn
from convert.adapters.solidworks.Resolved.FaceIdentity import (
    KCapClass, KEdgeClass, ReadFaceHead, ReadFaceReturn, ReadSurfaceId, SurfaceKey,
)
from convert.adapters.solidworks.Resolved.Cut.CutChooser import KCutClass
from convert.adapters.solidworks.Resolved.Cut.CutOpRead import ReadCutEnd
from convert.adapters.solidworks.Resolved.Cut.CutResultFace import KCutSelectors
from SolidWorksScopeSecondBoss import CAP_CLASS, EDGE_CLASS


def read_scope_surface(cursor):
    tag = ReadTag(cursor.BlobValue, cursor.Offset)
    class_name = cursor.Classes.get(tag.index)
    require(
        tag.kind == KClassRefKind and class_name in (KCapClass, KEdgeClass, CAP_CLASS, EDGE_CLASS),
        "unexpected scoped chooser surface class",
    )
    surface = ReadSurfaceId(cursor, class_name, IsCap=class_name == KCapClass)
    if class_name in KCutSelectors:
        fields = cursor.ReadInts("<2i")
        require(fields == KCutSelectors[class_name], "unexpected scoped chooser surface selectors")
        surface = {**surface, "extra_fields": fields, "end": cursor.Offset}
    return surface


def read_scope_chooser_face(cursor, cut, owner, classes, earlier_edges, cut_edges):
    header, count = ReadFaceHead(cursor, KClassRefKind, 768)
    surfaces = [read_scope_surface(cursor) for _ in range(count + 1)]
    cap_class, edge_class = classes
    prior, generated = [], []
    for surface in surfaces:
        file_ref, feature, clock, occurrence = SurfaceKey(surface)
        require(file_ref == cut["file_ref_object"], "scoped chooser face belongs to another file")
        if feature == owner[0]:
            require(clock == owner[1], "scoped chooser face has a different Boss clock")
            prior.append((surface["class"], occurrence))
        else:
            require(feature == cut["native_feature_id"] and surface["class"] == EDGE_CLASS,
                    "scoped chooser face has an unreached surface owner or class")
            generated.append(occurrence)
    if cut_edges is None:
        require(
            prior == [(cap_class, 0), *((edge_class, edge) for edge in earlier_edges)] and not generated,
            "scoped chooser face does not retain the reached Boss cap and ordered perimeter",
        )
    else:
        require(
            prior == [(cap_class, 0), (cap_class, 1)]
            and len(generated) == len(set(generated)) == 3 and set(generated) <= cut_edges,
            "scoped chooser face does not retain both Boss caps and three Cut contour sides",
        )
    ReadFaceReturn(cursor)
    return {**header, "surfaces": surfaces, "end": cursor.Offset}


def read_scope_chooser(cursor, cut, body, classes, clock, previous_edges, previous_centre, cut_edges):
    start = cursor.Offset
    _, _, chooser = cursor.TakePointer(("moPerBodyChooserData_c",), KClassRefKind, CompactOnly=True)
    require(cursor.ReadInts("<H") == (2,), "scoped chooser must own two faces")
    owner = (body["feature_id"], clock)
    faces = [
        read_scope_chooser_face(cursor, cut, owner, classes, previous_edges, None),
        read_scope_chooser_face(cursor, cut, owner, classes, (), cut_edges),
    ]
    centre_offset = cursor.Offset
    centre = ReadChoiceTail(cursor, KClassRefKind, ())
    require(centre["centre_and_scale"] == previous_centre, "scoped chooser centre differs from the reached Boss")
    return {
        "offset": start, "object_index": chooser, "body_id": body["body_id"],
        "feature_id": body["feature_id"], "faces": faces, "centre_offset": centre_offset,
        "centre": centre, "end": cursor.Offset, "next_map_index": cursor.NextIndex,
    }


def read_scope_partition(cursor, bodies):
    offset = cursor.Offset
    require(cursor.ReadInts("<H3i") == (0, 0, 0, 1), "unexpected scoped Cut partition framing")
    marker_offset = cursor.Offset
    _, _, marker = cursor.TakePointer(("moPMarkRecord_c",), KClassRefKind, CompactOnly=True)
    (state,) = cursor.ReadInts("<i")
    require(state == 19 and cursor.ReadInts("<4i") == (0, 0, 0, 0), "unexpected scoped Cut partition state")
    pairs_offset = cursor.Offset
    (count,) = cursor.ReadInts("<i")
    require(count == len(bodies), "scoped Cut partition and body counts differ")
    pairs = [cursor.ReadInts("<2i") for _ in range(count)]
    require(pairs == [(body["recent_atom_id"], body["body_id"]) for body in bodies],
            "scoped Cut partition and scope atom/body pairs differ")
    require(cursor.ReadInts("<8i") == (0,) * 8, "unexpected scoped Cut partition return")
    return {
        "offset": offset, "marker_offset": marker_offset, "object_index": marker,
        "state": state, "pairs_offset": pairs_offset, "atom_body_pairs": pairs, "end": cursor.Offset,
    }


def read_scope_terminal(cursor, recording, cap, previous_chooser, prefix):
    cut = recording["cut_node"]
    bodies = recording["cut_scope"]["bodies"]
    cut_edges = set(recording["cut_sketch"]["chain"]["edge_ids"])
    second_chooser = prefix["second_operation"]["choices"]
    second_clocks = prefix["second_archive_words"]["cap_clock_words"]
    require(len(set(second_clocks)) == 1, "different clocks on the reached second Boss caps")
    choosers = [
        read_scope_chooser(cursor, cut, bodies[0], (KCapClass, KEdgeClass), cap["clock_word"],
                           previous_chooser["side_occurrences"], previous_chooser["centre_and_scale"], cut_edges),
        read_scope_chooser(cursor, cut, bodies[1], (CAP_CLASS, EDGE_CLASS), second_clocks[0],
                           second_chooser["caps"][0]["edge_occurrences"],
                           second_chooser["centre"]["centre_and_scale"], cut_edges),
    ]
    generated = [
        [row for row in chooser["faces"][1]["surfaces"] if row["feature_id"] == cut["native_feature_id"]]
        for chooser in choosers
    ]
    require(
        {SurfaceKey(row) for row in generated[0]} == {SurfaceKey(row) for row in generated[1]}
        and len({row["time_word"] for row in generated[0]}) == 1,
        "scoped chooser bodies do not share the same Cut-side surface identities",
    )
    return_offset = cursor.Offset
    CheckChoiceOwn(cursor, cut, KCutClass)
    require(cursor.ReadInts("<3H") == (1, 1, 0), "unexpected empty secondary scoped chooser")
    CheckChoiceOwn(cursor, cut, KCutClass)
    require(cursor.ReadInts("<iH") == (0, 0), "unexpected scoped chooser return")
    partition = read_scope_partition(cursor, bodies)
    body_return = cursor.Offset
    ReadBodyReturn(cursor)
    extent = ReadCutEnd(cursor)
    require(extent["conditions"] == (1, 0) and extent["depth_display"] is None,
            "retained scoped Cut does not have a depthless through-all end")
    footer = cursor.Offset
    from_end_words_offset = footer - struct.calcsize("<5idi")
    from_end_words = struct.unpack_from("<5i", cursor.BlobValue, from_end_words_offset)
    require(cursor.ReadInts("<i") == (0,) and cursor.Offset == len(cursor.BlobValue),
            "scoped Cut does not close the resolved stream")
    return {
        "choosers": choosers, "chooser_return_offset": return_offset, "partition": partition,
        "body_return_offset": body_return, "end_specification": extent,
        "from_end_words_offset": from_end_words_offset, "from_end_words": from_end_words,
        "footer_offset": footer, "end": cursor.Offset, "next_map_index": cursor.NextIndex,
    }


def comparable_terminal(terminal):
    choosers = [
        {
            **chooser,
            "faces": [
                {**face, "surfaces": [{key: value for key, value in row.items() if key != "time_word"}
                                      for row in face["surfaces"]]}
                for face in chooser["faces"]
            ],
        }
        for chooser in terminal["choosers"]
    ]
    return {**terminal, "choosers": choosers, "from_end_words": terminal["from_end_words"][:4]}
