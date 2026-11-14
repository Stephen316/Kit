import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402


def main():
    rel, suffix = sys.argv[1], sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    with zipfile.ZipFile(ROOT / rel) as archive:
        member = next(name for name in archive.namelist() if name.endswith(suffix))
        data = archive.read(member)
    model = ReadJournal(data) if member.endswith(".smbh") else ReadGeometry(data)
    print(model.Header if hasattr(model, "Header") else "")
    for index, value in enumerate(model.Entities):
        print(index, repr(value)[:width])


main()
