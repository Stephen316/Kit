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


def block(toks, at):
    name = toks[at][1]
    at += 1
    d1 = toks[at][1]
    at += 1
    if toks[at][0] == 4:
        d2 = toks[at][1]
        at += 1
        rational = None
        if name == "nurbs":
            rational = toks[at][1]
            at += 1
        enums = [toks[at + k][1] for k in range(4)]
        at += 4
        nu = toks[at][1]
        nv = toks[at + 1][1]
        at += 2
        mu = sum(toks[at + 2 * k + 1][1] for k in range(nu))
        at += 2 * nu
        mv = sum(toks[at + 2 * k + 1][1] for k in range(nv))
        at += 2 * nv
        pu = mu - (d1 - 1)
        pv = mv - (d2 - 1)
        width = 4 if name == "nurbs" else 3
        at += pu * pv * width
        return at, f"BSS[{name},{d1}x{d2},{rational},{enums}]"
    closure = toks[at][1]
    at += 1
    count = toks[at][1]
    at += 1
    mult = sum(toks[at + 2 * k + 1][1] for k in range(count))
    at += 2 * count
    poles = mult - (d1 - 1)
    run = 0
    while at + run < len(toks) and toks[at + run][0] == 6:
        run += 1
    extra = 1 if name == "nurbs" else 0
    dim = None
    for candidate in (2, 3):
        need = poles * (candidate + extra)
        if run in (need, need + 1, need + 2):
            dim = candidate
            break
    if dim is None:
        dim = 3 if run >= poles * (3 + extra) else 2
    at += poles * (dim + extra)
    return at, f"BS{dim}[{name},{d1},c{closure}]"


def shape(toks):
    out = []
    at = 0
    while at < len(toks):
        tag, value = toks[at]
        if tag == 13 and value in ("nubs", "nurbs"):
            at, text = block(toks, at)
            out.append(text)
            continue
        if tag in (13, 14):
            out.append(f"<{value}>")
        elif tag == 6:
            out.append("d")
        elif tag == 4:
            out.append("i" if value not in (23100, 23200, 22500, 22600, 22300, 22506) else f"r{value}")
        elif tag == 21:
            out.append(f"e{value}")
        elif tag == 10:
            out.append("T")
        elif tag == 11:
            out.append("F")
        elif tag == 12:
            out.append("@")
        elif tag == 15:
            out.append("{")
        elif tag == 16:
            out.append("}")
        elif tag == 19:
            out.append("P")
        elif tag == 20:
            out.append("V")
        elif tag == 7:
            out.append(json.dumps(value))
        else:
            out.append(f"t{tag}")
        at += 1
    text = " ".join(out)
    while " d d" in text:
        text = text.replace(" d d", " d")
    return text


def main():
    rows = json.loads((BASE / "Inventory.json").read_text())
    shapes = collections.defaultdict(collections.Counter)
    errors = collections.Counter()
    for row in rows:
        if "names" not in row:
            continue
        if not any(key.split(":", 1)[1] in GEOM for key in row["names"]):
            continue
        with zipfile.ZipFile(ROOT / row["path"]) as archive:
            data = archive.read(row["member"])
        _, _, recs = AsmScan.records(data)
        for rec in recs:
            if rec["name"] not in GEOM:
                continue
            try:
                text = shape(rec["tokens"])
            except Exception as error:
                errors[repr(error)] += 1
                continue
            top = next((v for t, v in rec["tokens"][4:7] if t in (13, 14)), "-")
            shapes[f"{rec['name']}:{top}"][text] += 1
    out = {key: value.most_common() for key, value in sorted(shapes.items())}
    out["errors"] = errors.most_common()
    (BASE / "Shapes.json").write_text(json.dumps(out, indent=1))
    for key, value in sorted(shapes.items()):
        print(key, len(value), sum(value.values()))


main()
