from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack
import sys

ROOT = Path(__file__).resolve().parents[3]
CAPTURE_REVISION = "466dcb172dfa3803463e07ccde963ba01671d200"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/automation")]

from HeaderLogs import KDefaultIds, ReadHeaderLogs, WriteHeaderLogs
from SolidworksCensusInputs import capture_inputs
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import SldprtArchive


# Native feature order corroborates authored names independently of revision replication.
def verify_header_logs() -> dict[str, object]:
    rows, _ = capture_inputs(ROOT, CAPTURE_REVISION)
    captures = {}
    default_count = len(KDefaultIds) - 1
    for _, asset, source, _, measurement in rows:
        archive = SldprtArchive.from_bytes(source, asset["path"])
        RequireArch(ContainerMo(archive.streams), 19000, "ModelHeader generation")
        stream = archive.require("Contents/Config-0-ModelHeader")
        RequireArch(stream == archive.require("Header2"), True, "ModelHeader duplicate")
        cursor, state = ReadHeaderLogs(stream, 19000)
        _, update_stamp, _ = unpack("<3I", archive.require("ModelStamps"))
        RequireArch(state.UpdateStamp, update_stamp, "ModelHeader shared update stamp")
        saved = stream[: cursor.Offset]
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
        writer = WriteHeaderLogs(19000, state)
        RequireArch(
            writer.build() == saved,
            True,
            f"ModelHeader revision bytes for {asset['path']}",
        )
        RequireArch(
            (
                writer.next_index,
                {index: name for name, index in writer.classes.items()},
            ),
            (cursor.NextIndex, cursor.Classes),
            "ModelHeader live log allocator",
        )
        captures[asset["sha256"]] = sha256(saved).hexdigest()
    return {"capture_revision": CAPTURE_REVISION, "captures": captures}


if __name__ == "__main__":
    print(json.dumps(verify_header_logs(), sort_keys=True))
