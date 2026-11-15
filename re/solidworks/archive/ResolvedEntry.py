"""Replay the P04 resolved-list entry and its separately witnessed profiles."""

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


# both named record types inherit the guarded modern node concept and feature fields
def read_named_feature(cursor):
    from convert.adapters.solidworks.container.Archive import ReadString
    from SketchRoot import Require
    from SupportPlane import read_empty_label, read_feature_base

    name, length = ReadString(cursor.blob, cursor.position)
    cursor.position += length
    node_state, flags, node_id, node_tail = cursor.read("<iIii")
    Require((node_state, flags, node_tail), (0, 0x40000000, 0), "ordinary typed node")
    read_empty_label(cursor)
    Require(cursor.read("<i"), (0,), "empty lightweight child list")
    cursor.null()  # moVisualProperties_c
    Require(cursor.read("<Hi"), (0, 0), "empty resolved node list and tail")
    read_feature_base(cursor)
    return name, node_id


# folder suffixes are confined to the ordinary bodies at the start of these captures
def read_list_prefix(blob, config_map):
    from convert.adapters.solidworks.container.Archive import (
        KClassRefKind,
        KDefinitionKind,
    )
    from FaceOccurrence import FaceCursor
    from SketchRoot import Require

    base, count = unpack_from("<iH", blob)
    Require(base, config_map.NextIndex, "derived configuration map counter")
    Require(count, 21, "witnessed short resolved list")
    cursor = FaceCursor(
        blob,
        6,
        config_map.NextIndex,
        config_map.Classes.copy(),
        config_map.Objects.copy(),
    )
    folders = []
    for type_name, suffix in (
        ("moCommentsFolder_c", (0, 0)),
        ("moFavoriteFolder_c", (1, 0, 0, 1)),
        ("moHistoryFolder_c", (1,)),
    ):
        offset = cursor.position
        object_index = cursor.pointer(KDefinitionKind, type_name)
        cursor.pointer(KClassRefKind, "moNodeName_c")
        name, feature_id = read_named_feature(cursor)
        Require(cursor.read(f"<{len(suffix)}i"), suffix, f"guarded {type_name} scalars")
        folders.append(
            {
                "class": type_name,
                "name": name,
                "native_feature_id": feature_id,
                "object_index": object_index,
                "offset": offset,
                "cursor": cursor.position,
                "next_map_index": cursor.next_index,
            }
        )
    return {
        "list_count": count,
        "prior_map_index": base,
        "folders": folders,
        "stopped_in": "moHistoryFolder_c",
    }


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
    name, feature_id = read_named_feature(cursor)
    cursor.read("<i")  # moModelFeature_c
    Require(cursor.read("<i"), (0,), "guarded scalar before the early profile pointer")
    early_pointer = cursor.position
    cursor.null()
    Require(cursor.read("<i"), (0,), "guarded scalar after the early profile pointer")
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


# stream hashes prevent earlier native checkpoints from being reused on changed files
def read_capture(root, asset, control):
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
    resolved_pin = WINDOWS[name]
    Require(
        sha256(config).hexdigest(),
        control["config_sha256"],
        "pinned configuration stream",
    )
    Require(
        sha256(resolved).hexdigest(), resolved_pin["sha256"], "pinned resolved stream"
    )
    config_map, _ = ReadConfigMap(config, KApplicationBuild)
    prefix = read_list_prefix(resolved, config_map)
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
        "measured profile names and identities",
    )
    return {
        "file": name,
        "native_sha256": digest,
        "config_sha256": control["config_sha256"],
        "resolved_sha256": resolved_pin["sha256"],
        "native_handoff_witness_sha256": control["handoff_sha256"],
        "native_profile_witness_sha256": control["link_sha256"],
        "list_prefix": prefix,
        "separately_witnessed_profiles": profiles,
    }


# the report preserves the distinct sources of entry and profile provenance
def main():
    ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "src"))
    receipt, _ = ReadReceipts(root)
    assets = {asset["file"]: asset for asset in receipt["native_files"]}
    evidence = {
        "scope": "p04_resolved_entry_research",
        "capture_revision": KCaptureRev,
        "capture_receipt_sha256": KReceiptDigest,
        "application_build": KApplicationBuild,
        "captures": [
            read_capture(root, assets[name], control)
            for name, control in CONTROLS.items()
        ],
    }
    output = json.dumps(evidence, sort_keys=True, indent=2, allow_nan=False)
    sys.stdout.buffer.write((output + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
