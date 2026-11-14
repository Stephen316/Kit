from collections import Counter
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json


def inventory(root: Path) -> dict:
    rows = []
    methods = Counter()
    for path in sorted((root / "re/Fusion/Study").rglob("*.f3d")):
        data = path.read_bytes()
        with ZipFile(path) as archive:
            entries = archive.infolist()
            counts = Counter(str(entry.compress_type) for entry in entries)
        methods.update(counts)
        rows.append({
            "path": str(path.relative_to(root)),
            "sha256": sha256(data).hexdigest(),
            "size": len(data),
            "members": len(entries),
            "compression_methods": dict(counts),
        })
    return {
        "scope": "ZIP central-directory inventory only; no codec or tests executed",
        "archives": len(rows),
        "members": sum(row["members"] for row in rows),
        "compression_methods": dict(methods),
        "files": rows,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    destination = Path(__file__).with_name("CorpusInventory.json")
    destination.write_text(json.dumps(inventory(root), indent=2) + "\n")
