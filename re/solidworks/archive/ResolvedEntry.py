"""Replay the P04 resolved-list entry through the blind boss end-specification prefix."""

from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys

from FaceEvidence import WINDOWS
from ResolvedPrelude import (
    read_named_concept,
    read_profile_body_prefix,
    read_resolved_prelude,
)
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
