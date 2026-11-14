"""Corpus conventions that general NURBS authoring must follow.

Reads every byte-exact `.smb` member with the production reader and tallies
B-spline closure and singularity forms, edges without curves, pcurve presence by
carrier type, faces with several loops and seam edges. For every B-spline
surface it also records which pole rows or columns collapse to one point next
to the singular codes, whether the closed directions repeat their end poles,
and along which direction the weights of each rational form vary.
"""

import collections
import dataclasses
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.PoleCount import PoleCount  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode  # noqa: E402


def walk(value, sink, owner):
    if isinstance(value, (BsCurve, BsSurface)):
        sink.append((owner, value))
        return
    if isinstance(value, tuple):
        for item in value:
            walk(item, sink, owner)
        return
    if dataclasses.is_dataclass(value):
        name = getattr(value, "SubtypeName", owner)
        for field in dataclasses.fields(value):
            walk(getattr(value, field.name), sink, name)


def ends(degree, mult):
    return f"ends={mult[0] - degree:+d}/{mult[-1] - degree:+d}"


def same(points, tolerance=1e-9):
    return all(max(abs(a - b) for a, b in zip(point, points[0])) <= tolerance for point in points)


def surface_form(value):
    ucount = PoleCount(value.UDegree, value.UMultiplicity)
    vcount = PoleCount(value.VDegree, value.VMultiplicity)
    rows = [value.Poles[row * ucount:(row + 1) * ucount] for row in range(vcount)]
    cols = [value.Poles[col::ucount] for col in range(ucount)]
    weights = value.Weights or (1.0,) * len(value.Poles)
    wrows = [weights[row * ucount:(row + 1) * ucount] for row in range(vcount)]
    singular = f"using={value.USingular} vsing={value.VSingular} collapsed ulow={same(cols[0])} uhigh={same(cols[-1])} vlow={same(rows[0])} vhigh={same(rows[-1])}"
    closure = f"uclosure={value.UClosure} vclosure={value.VClosure} uends_equal={all(same([row[0], row[-1]]) for row in rows)} vends_equal={same(list(rows[0]) + list(rows[-1])) or all(same([a, b]) for a, b in zip(rows[0], rows[-1]))}"
    ratio = lambda row: [w / row[0] for w in row]
    along_v = all(same([[w] for w in wrow]) for wrow in wrows)
    along_u = all(max(abs(a - b) for a, b in zip(ratio(wrow), ratio(wrows[0]))) <= 1e-9 for wrow in wrows)
    rational = f"rational={value.Rational} form={value.RationalForm!r} weights_vary_only_in_v={along_v} weights_separable={along_u}"
    return singular, closure, rational


def carrier(entities, face):
    surface = entities[face.Surface]
    if isinstance(surface, SplineNode):
        inner = surface.Surface
        return "spline:" + getattr(inner, "SubtypeName", type(inner).__name__)
    return type(surface).__name__


def main():
    verify = json.loads((BASE / "VerifyAll.json").read_text())
    stats = {key: collections.Counter() for key in ("bsplines", "singular", "closure", "rational", "curveless", "pcurves", "loops", "seams", "examples")}
    examples = collections.defaultdict(list)
    for member in verify["members"]:
        if member["status"] != "exact" or not member["member"].endswith(".smb"):
            continue
        with zipfile.ZipFile(ROOT / member["path"]) as archive:
            entities = ReadGeometry(archive.read(member["member"])).Entities
        label = member["path"].split("/")[-1]
        found = []
        for value in entities:
            if isinstance(value, (SplineNode, PcurveNode)) or type(value).__name__ == "IntcurveNode":
                walk(value, found, type(value).__name__)
        for owner, value in found:
            if isinstance(value, BsSurface):
                key = f"surface owner={owner} uclosure={value.UClosure} vclosure={value.VClosure} using={value.USingular} vsing={value.VSingular} u{ends(value.UDegree, value.UMultiplicity)} v{ends(value.VDegree, value.VMultiplicity)}"
            else:
                key = f"curve{value.Dimension} owner={owner} closure={value.Closure} {ends(value.Degree, value.Multiplicity)}"
            stats["bsplines"][key] += 1
            if isinstance(value, BsSurface):
                singular, closure, rational = surface_form(value)
                if value.USingular or value.VSingular:
                    stats["singular"][singular] += 1
                if value.UClosure or value.VClosure:
                    stats["closure"][closure] += 1
                stats["rational"][rational] += 1
            if len(examples[key]) < 2:
                examples[key].append(label)
        loops_of = collections.defaultdict(list)
        for index, value in enumerate(entities):
            if isinstance(value, LoopNode):
                loops_of[value.OwnerFace].append(index)
        for index, value in enumerate(entities):
            if isinstance(value, FaceNode):
                kind = carrier(entities, value)
                stats["loops"][f"{kind} loops={min(len(loops_of[index]), 3)}"] += 1
                if len(loops_of[index]) > 1 and len(examples["loops:" + kind]) < 2:
                    examples["loops:" + kind].append(label)
        face_of_coedge = {}
        for index, value in enumerate(entities):
            if isinstance(value, CoedgeNode):
                face = entities[value.OwnerLoop].OwnerFace
                face_of_coedge[index] = face
                stats["pcurves"][f"{carrier(entities, entities[face])} pcurve={'set' if value.Pcurve >= 0 else 'none'}"] += 1
        for index, value in enumerate(entities):
            if isinstance(value, EdgeNode):
                uses = [c for c, v in enumerate(entities) if isinstance(v, CoedgeNode) and v.EdgeRef == index]
                faces = {face_of_coedge[c] for c in uses}
                if value.CurveRef < 0:
                    key = f"same_vertex={value.StartVertex == value.EndVertex} uses={len(uses)} carriers={sorted(carrier(entities, entities[f]) for f in faces)} params=({value.StartParam:g},{value.EndParam:g})"
                    stats["curveless"][key] += 1
                    if len(examples["curveless:" + key]) < 2:
                        examples["curveless:" + key].append(label)
                if len(uses) == 2 and len(faces) == 1:
                    face = next(iter(faces))
                    pcs = [entities[c].Pcurve for c in uses]
                    offsets = [(entities[p].OffsetU, entities[p].OffsetV) if p >= 0 and isinstance(entities[p], PcurveNode) else None for p in pcs]
                    key = f"{carrier(entities, entities[face])} senses={sorted(entities[c].Reversed for c in uses)} pcurves={['set' if p >= 0 else 'none' for p in pcs]} offsets={offsets}"
                    stats["seams"][key] += 1
                    if len(examples["seam:" + key]) < 2:
                        examples["seam:" + key].append(label)
    report = dict(
        script="re/Fusion/Reconstruction/ComplexGeometry/SurveyTopology.py",
        scope="byte-exact .smb members of VerifyAll.json",
        ends="end multiplicity minus degree at the low and high end",
        **{key: [dict(key=k, count=c) for k, c in value.most_common()] for key, value in stats.items() if key != "examples"},
        examples=dict(examples),
    )
    (BASE / "SurveyTopology.json").write_text(json.dumps(report, indent=1) + "\n")
    for key, value in stats.items():
        print("==", key)
        for k, c in value.most_common(40):
            print(c, k)


main()
