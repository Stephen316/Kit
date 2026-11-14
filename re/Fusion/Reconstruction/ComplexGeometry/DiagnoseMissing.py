"""List records whose required references are -1 in one snapshot member."""
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntitiesMut import ReadEntitiesMut  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadModelHead import ReadModelHead  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Validation.RequiredRefs import KRequiredRefs  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode  # noqa: E402
from convert.formats.Fusion.MetaCursor import MetaCursor  # noqa: E402


def main():
    rel, suffix = sys.argv[1], sys.argv[2]
    with zipfile.ZipFile(ROOT / rel) as archive:
        payload = archive.read(next(name for name in archive.namelist() if name.endswith(suffix)))
    cursor = MetaCursor(payload)
    ReadModelHead(cursor, False)
    records = [MakeEntityNode(value) for value in ReadEntitiesMut(cursor, "End-of-ASM-data")]
    for index, record in enumerate(records):
        for position in KRequiredRefs.get(record.Name, ()):
            if record.Tokens[position] == (12, -1):
                print(index, record.Name, "missing", position, record.Tokens[:12])


main()
