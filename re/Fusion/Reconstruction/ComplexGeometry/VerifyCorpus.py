import collections
import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402

GEOM = ("spline-surface", "intcurve-curve", "pcurve", "tcoedge-coedge", "tedge-edge", "tvertex-vertex")


def run(data, history):
    model = ReadJournal(data) if history else ReadGeometry(data)
    out = EmitJournal(model) if history else EmitGeometry(model)
    return model, out


def main():
    scope = sys.argv[1] if len(sys.argv) > 1 else "complex"
    rows = json.loads((BASE / "Inventory.json").read_text())
    results = []
    status = collections.Counter()
    failures = collections.Counter()
    started = time.time()
    for row in rows:
        if "names" not in row:
            continue
        names = {key.split(":", 1)[1] for key in row["names"]}
        complex_member = bool(names & set(GEOM))
        if scope == "complex" and not complex_member:
            continue
        with zipfile.ZipFile(ROOT / row["path"]) as archive:
            data = archive.read(row["member"])
        history = row["member"].endswith(".smbh")
        entry = {"path": row["path"], "member": row["member"], "sha256": row["sha256"], "complex": complex_member,
                 "before": row.get("production")}
        try:
            _, out = run(data, history)
            entry["exact"] = out == data
            entry["status"] = "exact" if out == data else "mismatch"
            entry["emittedSha256"] = hashlib.sha256(out).hexdigest()
        except Exception as error:
            entry["status"] = "error"
            entry["error"] = str(error)[:200]
            failures[str(error)[:120]] += 1
        status[(complex_member, entry["status"])] += 1
        results.append(entry)
    summary = {
        "scope": scope,
        "members": len(results),
        "status": {f"{'complex' if key[0] else 'other'}:{key[1]}": value for key, value in sorted(status.items())},
        "failures": failures.most_common(),
        "seconds": round(time.time() - started, 1),
    }
    name = "VerifyComplex.json" if scope == "complex" else "VerifyAll.json"
    (BASE / name).write_text(json.dumps({"summary": summary, "members": results}, indent=1))
    print(json.dumps(summary, indent=1))


main()
