from hashlib import sha256
import json
from pathlib import Path
from struct import calcsize
import sys

ROOT = Path(__file__).resolve().parents[3]
CAPTURE_REVISION = "466dcb172dfa3803463e07ccde963ba01671d200"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/automation")]

from CmgrColorReadback import ReadColorSpan
from CmgrTail import KListClass, ReadCmgrTail, WriteCmgrTail
from ColorAppearance import EncodeColorDspbr
from SolidworksCensusInputs import capture_inputs
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    ContainerMo,
    ReadTag,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Definition import ArchiveWriter

TREE_IDS = {"P01": (), "P03": (34,), "P04": (34, 46)}


# the witnessed second list reference anchors the typed terminal scan from EOF
def verify_tail(stream, tree_ids, asset):
    second_list = len(stream) - 70
    reference = ReadTag(stream, second_list)
    RequireArch(
        (reference.kind, reference.size), (KClassRefKind, 2), "CMgr second list"
    )
    index = reference.index
    RequireArch(index is not None, True, "CMgr list class allocation")
    first_list = (
        second_list
        - calcsize("<HHH")
        - len(KListClass)
        - calcsize("<Hi3iIi")
        - len(tree_ids) * calcsize("<iII")
    )
    cursor = ArchiveCursor(stream, first_list, index, {}, {})
    stamps = ReadCmgrTail(cursor, 19000)
    RequireArch(tuple(stamp.tree_id for stamp in stamps), tree_ids, "CMgr feature IDs")
    writer = ArchiveWriter()
    writer.SetNextIndex(index)
    WriteCmgrTail(writer, 19000, stamps)
    RequireArch(writer.next_index, cursor.NextIndex, "CMgr terminal allocations")
    RequireArch(
        writer.build() == stream[first_list:], True, f"complete CMgr tail in {asset}"
    )
    return sha256(stream[first_list:]).hexdigest()


# the emitted default color body must occupy exactly the independently framed span
def verify_color():
    rows, _ = capture_inputs(ROOT, CAPTURE_REVISION)
    captures = {}
    tails = {}
    for recipe, item, data, _, _ in rows:
        archive = SldprtArchive.from_bytes(data, item["path"])
        generation = ContainerMo(archive.streams)
        RequireArch(generation, 19000, "CMgr verification generation")
        stream = archive.require("Contents/CMgr")
        color, start, end = ReadColorSpan(stream, 19000)
        saved = stream[start:end]
        RequireArch(end - start, 300, "CMgr default DSPBR body width")
        RequireArch(
            EncodeColorDspbr(19000, color) == saved,
            True,
            f"CMgr default DSPBR reconstruction for {item['path']}",
        )
        captures[item["sha256"]] = sha256(saved).hexdigest()
        tails[item["sha256"]] = verify_tail(stream, TREE_IDS[recipe], item["path"])
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "terminal_records": tails,
    }


if __name__ == "__main__":
    print(json.dumps(verify_color(), sort_keys=True))
