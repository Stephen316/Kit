import hashlib
import json
import lzma
import runpy
from pathlib import Path


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
TOOLS = runpy.run_path(str(BASE.parent / "OgsScene/DecodeOgs.py"))


def main():
    sources = sorted((ROOT / "re/Fusion/LocalOracle/ParaMesh").glob("vendor_*.f3d"))
    report = {"scope": "Read-only inspection of native-saved mesh graphics; explicit unresolved callback boundaries retained", "sources": [TOOLS["inspect"](source) for source in sources]}
    data = lzma.compress((json.dumps(report, indent=2) + "\n").encode())
    (BASE / "SavedWorlds.json.xz").write_bytes(data)
    summary = {"details": "SavedWorlds.json.xz", "sha256": hashlib.sha256(data).hexdigest(), "sources": [{"source": row["source"], "world_bytes": row["world"]["size"], "consumed_prefix": row["world"]["decodedPrefixEnd"], "unresolved": row["world"]["unresolved"], "mesh_bytes": row["mesh"]["size"]} for row in report["sources"]]}
    (BASE / "SavedWorlds.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
