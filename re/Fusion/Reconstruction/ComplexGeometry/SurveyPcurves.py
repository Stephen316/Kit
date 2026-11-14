import collections
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import SubtypeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402


def main():
    data = json.loads((BASE / "VerifyComplex.json").read_text())
    stats = collections.Counter()
    for member in data["members"]:
        if member["status"] != "exact":
            continue
        with zipfile.ZipFile(ROOT / member["path"]) as archive:
            payload = archive.read(member["member"])
        model = ReadJournal(payload) if member["member"].endswith(".smbh") else ReadGeometry(payload)
        entities = model.Entities
        for value in entities:
            if not isinstance(value, CoedgeNode) or value.Pcurve < 0:
                continue
            pcurve = entities[value.Pcurve]
            edge = entities[value.EdgeRef]
            if not isinstance(pcurve, PcurveNode):
                stats["notpcurve"] += 1
                continue
            key = [f"sense={'flipped' if value.Reversed != pcurve.Reversed else 'same'}", f"form={pcurve.Form}", f"partner={value.Partner >= 0}"]
            if pcurve.Form == 0 and isinstance(pcurve.Curve, SubtypeNode):
                curve = pcurve.Curve.Body.Spline
                lower, upper = curve.Knots[0], curve.Knots[-1]
                same = abs(lower - edge.StartParam) < 1e-9 and abs(upper - edge.EndParam) < 1e-9
                negated = abs(lower + edge.EndParam) < 1e-9 and abs(upper + edge.StartParam) < 1e-9
                key.append("range=" + ("symmetric" if same and negated else "edge" if same else "negated" if negated else "other"))
                key.append(f"offsets={pcurve.OffsetU != 0 or pcurve.OffsetV != 0}")
            stats[" ".join(key)] += 1
    rows = [dict(count=count, key=key) for key, count in stats.most_common()]
    (BASE / "SurveyPcurves.json").write_text(json.dumps(dict(script="re/Fusion/Reconstruction/ComplexGeometry/SurveyPcurves.py", scope="coedges with a pcurve in the exact complex members of VerifyComplex.json", sense="coedge Reversed compared with the pcurve Reversed flag", rows=rows), indent=1) + "\n")
    for row in rows:
        print(row["count"], row["key"])


main()
