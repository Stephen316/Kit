from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
CAPTURE_REVISION = "466dcb172dfa3803463e07ccde963ba01671d200"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/automation")]

from CmgrColorReadback import ReadColorSpan
from ColorAppearance import EncodeColorDspbr
from SolidworksCensusInputs import capture_inputs
from convert.adapters.solidworks.container.Archive import ContainerMo
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.Container import SldprtArchive


# the emitted default color body must occupy exactly the independently framed span
def verify_color():
    rows, _ = capture_inputs(ROOT, CAPTURE_REVISION)
    captures = {}
    for _, item, data, _, _ in rows:
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
    return {"capture_revision": CAPTURE_REVISION, "captures": captures}


if __name__ == "__main__":
    print(json.dumps(verify_color(), sort_keys=True))
