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

SURF = {"exact_spl_sur", "sweep_sur", "VBL_SURF", "cyl_spl_sur", "loft_spl_sur", "cl_loft_spl_sur",
        "srf_srf_v_bl_spl_sur", "sum_spl_sur", "helix_spl_line", "g2_blend_spl_sur", "rb_blend_spl_sur", "off_spl_sur"}
CURV = {"exact_int_cur", "par_int_cur", "spring_int_cur", "int_int_cur", "helix_int_cur"}


def walk(rows, mode):
    table = []
    stats = collections.Counter()
    for rec in rows:
        if mode == "section" and rec.get("reset"):
            table = []
        toks = rec["tokens"]
        for index, (tag, value) in enumerate(toks):
            if tag == 15 and index + 1 < len(toks) and toks[index + 1][0] in (13, 14):
                name = toks[index + 1][1]
                if name == "ref":
                    target = toks[index + 2][1]
                    prev = toks[index - 2] if index >= 2 else None
                    kind = None
                    if prev and prev[0] == 13 and prev[1] == "spline":
                        kind = "surf"
                    elif rec["name"] == "spline-surface" and index == 4:
                        kind = "surf"
                    elif rec["name"] == "intcurve-curve" and index == 4:
                        kind = "curv"
                    elif prev and prev[0] == 13 and prev[1] == "intcurve":
                        kind = "curv"
                    if not 0 <= target < len(table):
                        stats["outOfRange"] += 1
                        continue
                    defined = table[target]
                    ok = (kind == "surf" and defined in SURF) or (kind == "curv" and defined in CURV)
                    stats[f"{kind}:{'ok' if ok else 'bad:' + defined}"] += 1
                else:
                    table.append(name)
    return stats


def main():
    rows = json.loads((BASE / "Inventory.json").read_text())
    total = {"stream": collections.Counter(), "section": collections.Counter()}
    for row in rows:
        if "names" not in row or not any(k in row["subtypes"] for k in row["subtypes"]):
            continue
        if not any(k.endswith(":ref") or ">ref" in k for k in list(row["subtypes"]) + list(row["nested"])):
            continue
        with zipfile.ZipFile(ROOT / row["path"]) as archive:
            data = archive.read(row["member"])
        _, _, recs = AsmScan.records(data)
        last = None
        for rec in recs:
            rec["reset"] = last is not None and rec["section"] != last
            last = rec["section"]
        for mode in total:
            total[mode].update(walk(recs, mode))
    print(json.dumps({k: dict(v) for k, v in total.items()}, indent=1))


main()
