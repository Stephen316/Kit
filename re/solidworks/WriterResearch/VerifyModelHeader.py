from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack
import sys

ROOT = Path(__file__).resolve().parents[3]
CAPTURE_REVISION = "466dcb172dfa3803463e07ccde963ba01671d200"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/automation")]

from HeaderLogs import KDefaultIds, ReadHeaderLogs
from HeaderSelf import ReadHeaderSelf
from HeaderTail import (
    KFrameTolerance,
    BoundPoints,
    HeaderBounds,
    ReadHeaderTail,
    WriteModelHdr,
)
from SolidworksCensusInputs import capture_inputs
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import SldprtArchive

AXES = {"Front Plane": 2, "Right Plane": 0}
FRAME_OFFSET = 58
FRAME_WIDTH = 80


# The licensed sketch and ordinary boss measurements determine the world box.
def measured_bounds(measurement) -> HeaderBounds:
    (sketch,) = [
        item for item in measurement["sketches"] if item["name"] == "RectangleSketch"
    ]
    points = tuple(
        (point[0] / 1000, point[1] / 1000, point[2] / 1000)
        for entity in sketch["entities"]
        if not entity["construction"]
        for point in (entity["start_world_mm"], entity["end_world_mm"])
    )
    RequireArch(len(points), 8, "ModelHeader measured rectangle")
    if not measurement["body_count"]:
        return BoundPoints(points)
    (boss,) = [
        item["operation"]
        for item in measurement["feature_tree"]
        if item["name"] == "BlindBoss"
    ]
    RequireArch(
        (boss["end_condition"], boss["both_directions"]),
        (0, False),
        "ModelHeader measured blind boss",
    )
    axis = AXES[sketch["support_name"]]
    depth = -boss["depth_m"] if boss["reverse_direction"] else boss["depth_m"]
    displacement = (depth if axis == 0 else 0.0, 0.0, depth if axis == 2 else 0.0)
    return BoundPoints(
        points
        + tuple(
            (x + displacement[0], y + displacement[1], z + displacement[2])
            for x, y, z in points
        )
    )


# Native feature order corroborates authored names independently of revision replication.
def verify_model_header() -> dict[str, object]:
    rows, _ = capture_inputs(ROOT, CAPTURE_REVISION)
    captures = {}
    headers = {}
    default_count = len(KDefaultIds) - 1
    for _, asset, source, _, measurement in rows:
        archive = SldprtArchive.from_bytes(source, asset["path"])
        RequireArch(ContainerMo(archive.streams), 19000, "ModelHeader generation")
        stream = archive.require("Contents/Config-0-ModelHeader")
        RequireArch(stream == archive.require("Header2"), True, "ModelHeader duplicate")
        cursor, state = ReadHeaderLogs(stream, 19000)
        prefix = stream[: cursor.Offset]
        actual = tuple(log.Name for log in state.Revisions[1:])
        measured = tuple(feature["name"] for feature in measurement["feature_tree"])
        RequireArch(
            Counter(actual[:default_count]),
            Counter(measured[:default_count]),
            "ModelHeader default tree members",
        )
        RequireArch(
            actual[default_count:],
            measured[default_count:],
            "ModelHeader ordered authored feature names",
        )
        self_reference = ReadHeaderSelf(cursor, 19000)
        frame_start = cursor.Offset + FRAME_OFFSET
        frame_end = frame_start + FRAME_WIDTH
        tail = ReadHeaderTail(cursor, 19000)
        RequireArch(
            (tail.CreationTime, state.UpdateStamp, tail.BodyStamp),
            unpack("<3I", archive.require("ModelStamps")),
            "ModelHeader shared document stamps",
        )
        bounds = measured_bounds(measurement)
        writer = WriteModelHdr(
            19000, state, self_reference, replace(tail, Bounds=bounds)
        )
        generated = writer.build()
        RequireArch(len(generated), len(stream), "ModelHeader complete length")
        RequireArch(
            generated[:frame_start] == stream[:frame_start]
            and generated[frame_end:] == stream[frame_end:],
            True,
            f"ModelHeader nongeometric bytes for {asset['path']}",
        )
        generated_frame = unpack("<10d", generated[frame_start:frame_end])
        native_frame = unpack("<10d", stream[frame_start:frame_end])
        RequireArch(
            all(
                abs(emitted - saved) <= KFrameTolerance
                for emitted, saved in zip(generated_frame, native_frame, strict=True)
            ),
            True,
            "ModelHeader measured world frame",
        )
        RequireArch(
            (
                writer.next_index,
                {index: name for name, index in writer.classes.items()},
            ),
            (cursor.NextIndex, cursor.Classes),
            "ModelHeader complete archive allocator",
        )
        captures[asset["sha256"]] = sha256(prefix).hexdigest()
        headers[asset["sha256"]] = sha256(stream).hexdigest()
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "model_header_records": headers,
    }


if __name__ == "__main__":
    print(json.dumps(verify_model_header(), sort_keys=True))
