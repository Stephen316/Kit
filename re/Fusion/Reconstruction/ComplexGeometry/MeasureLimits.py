import collections
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(BASE))

import AsmScan  # noqa: E402

GEOM = ("spline-surface", "intcurve-curve", "pcurve", "tcoedge-coedge", "tedge-edge", "tvertex-vertex", "wire")


def main():
    rows = json.loads((BASE / "Inventory.json").read_text())
    stats = collections.Counter()
    maxtok = collections.Counter()
    entities = []
    samples = collections.defaultdict(list)
    for row in rows:
        if "names" not in row or not any(key.split(":", 1)[1] in GEOM for key in row["names"]):
            continue
        with zipfile.ZipFile(ROOT / row["path"]) as archive:
            data = archive.read(row["member"])
        _, _, recs = AsmScan.records(data)
        active = sum(1 for rec in recs if rec["section"] == "active")
        archived = sum(1 for rec in recs if rec["section"] == "archived")
        entities.append((active + archived, row["member"].rsplit("/", 1)[-1], len(data)))
        for rec in recs:
            name = rec["name"]
            maxtok[name] = max(maxtok[name], len(rec["tokens"]))
            toks = rec["tokens"]
            if name in ("coedge", "tcoedge-coedge"):
                stats[f"{name}:i9={toks[9][1]}:pc={'set' if toks[10][1] != -1 else 'none'}"] += 1
            if name == "tvertex-vertex":
                stats[f"tvertex:{toks[6][1]}:{toks[9][1]}"] += 1
            if name == "tedge-edge":
                stats[f"tedge:{toks[12][1]}:{toks[13][1]}"] += 1
            if name == "pcurve":
                stats[f"pcurve:sel={toks[3][1]}"] += 1
            if name in ("tcoedge-coedge", "tedge-edge", "tvertex-vertex", "wire") and len(samples[name]) < 2:
                samples[name].append(toks)
            if name in ("body", "shell", "lump") and any(t == 12 for t, _ in toks):
                pass
    entities.sort(reverse=True)
    print(json.dumps({"stats": stats, "maxTokens": maxtok, "largest": entities[:20]}, indent=0, default=str))
    for name, items in samples.items():
        for toks in items:
            print(name, toks)


main()
