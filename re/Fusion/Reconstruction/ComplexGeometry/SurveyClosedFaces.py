"""Seams and collapsed sides of corpus spline faces.

Reads every byte-exact `.smb` member of VerifyBounds.json with the production
reader. For each face on a `spline-surface` record whose first B-spline block has a
singular code, it records the loop: each use, its edge, whether the edge has a
curve, whether the edge is closed, and whether the edge is used twice in the loop
(a seam). It also counts the edges without a curve in the same members and the
carrier types of the faces that use them, so the singular-side convention can be
told apart from the degenerate edges of other features.

For every edge used twice in one spline face, it records the offsets of the forward
use and of the reversed use. SurveyTopology.json lists the senses sorted but the
offsets in entity order, so it cannot say which use carries the offset.

Run with /opt/homebrew/bin/python3.14 -I. Writes SurveyClosedFaces.json beside it.
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

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode  # noqa: E402


def first_surface(value):
    if isinstance(value, BsSurface):
        return value
    if isinstance(value, tuple):
        for item in value:
            found = first_surface(item)
            if found is not None:
                return found
        return None
    if dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            found = first_surface(getattr(value, field.name))
            if found is not None:
                return found
    return None


def carrier_name(entities, face):
    surface = entities[face.Surface]
    if isinstance(surface, SplineNode):
        return "spline:" + getattr(surface.Surface, "SubtypeName", type(surface.Surface).__name__)
    return type(surface).__name__


def loop_uses(entities, loop_index):
    uses = []
    seen = set()
    index = entities[loop_index].FirstCoedge
    while index >= 0 and index not in seen:
        seen.add(index)
        coedge = entities[index]
        uses.append(coedge)
        index = coedge.NextCoedge
    return uses


def main():
    verify = json.loads((BASE / "VerifyBounds.json").read_text())
    faces = []
    curveless = collections.Counter()
    seams = collections.Counter()
    members = 0
    for member in verify["members"]:
        if member["status"] != "exact" or not member["member"].endswith(".smb"):
            continue
        members += 1
        with zipfile.ZipFile(ROOT / member["path"]) as archive:
            entities = ReadGeometry(archive.read(member["member"])).Entities
        for value in entities:
            if isinstance(value, CoedgeNode):
                edge = entities[value.EdgeRef]
                if isinstance(edge, EdgeNode) and edge.CurveRef < 0:
                    loop = entities[value.OwnerLoop]
                    curveless[carrier_name(entities, entities[loop.OwnerFace])] += 1
        users = collections.defaultdict(list)
        for index, value in enumerate(entities):
            if isinstance(value, CoedgeNode):
                users[value.EdgeRef].append(index)
        for edge, uses in users.items():
            if len(uses) != 2:
                continue
            owners = {entities[entities[use].OwnerLoop].OwnerFace for use in uses}
            if len(owners) != 1:
                continue
            face = entities[next(iter(owners))]
            if not isinstance(entities[face.Surface], SplineNode):
                continue
            offsets = {}
            for use in uses:
                coedge = entities[use]
                pcurve = entities[coedge.Pcurve] if coedge.Pcurve >= 0 else None
                offsets["reversed" if coedge.Reversed else "forward"] = [pcurve.OffsetU, pcurve.OffsetV] if isinstance(pcurve, PcurveNode) else None
            if set(offsets) != {"forward", "reversed"}:
                seams[f"{carrier_name(entities, face)} senses=same"] += 1
                continue
            seams[f"{carrier_name(entities, face)} forward={offsets['forward']} reversed={offsets['reversed']}"] += 1
        for index, value in enumerate(entities):
            if not isinstance(value, FaceNode) or value.Surface < 0 or not isinstance(entities[value.Surface], SplineNode):
                continue
            surface = first_surface(entities[value.Surface].Surface)
            if surface is None or not (surface.USingular or surface.VSingular):
                continue
            loops = []
            loop_index = value.FirstLoop
            while loop_index >= 0:
                uses = loop_uses(entities, loop_index)
                edges = collections.Counter(use.EdgeRef for use in uses)
                rows = []
                for use in uses:
                    edge = entities[use.EdgeRef]
                    rows.append(dict(edge=use.EdgeRef, reversed=use.Reversed, hasCurve=edge.CurveRef >= 0, closed=edge.StartVertex == edge.EndVertex, seam=edges[use.EdgeRef] == 2, hasPcurve=use.Pcurve >= 0))
                loops.append(rows)
                loop_index = entities[loop_index].NextLoop
            faces.append(dict(path=member["path"], member=member["member"], face=index, carrier=carrier_name(entities, value), uSingular=surface.USingular, vSingular=surface.VSingular, uClosure=surface.UClosure, vClosure=surface.VClosure, loops=loops))
    summary = collections.Counter()
    for face in faces:
        for rows in face["loops"]:
            shape = f"uses={len(rows)} seams={sum(1 for row in rows if row['seam']) // 2} closed={sum(1 for row in rows if row['closed'])} curveless={sum(1 for row in rows if not row['hasCurve'])}"
            summary[shape] += 1
    result = dict(
        script="re/Fusion/Reconstruction/ComplexGeometry/SurveyClosedFaces.py",
        scope="byte-exact .smb members of VerifyBounds.json",
        members=members,
        singularFaces=len(faces),
        loopShapes=[dict(key=key, count=count) for key, count in summary.most_common()],
        curvelessUsesByCarrier=[dict(key=key, count=count) for key, count in curveless.most_common()],
        seamOffsets=[dict(key=key, count=count) for key, count in seams.most_common()],
        faces=faces,
    )
    (BASE / "SurveyClosedFaces.json").write_text(json.dumps(result, indent=1) + "\n")
    print(members, len(faces), summary.most_common(), curveless.most_common())
    for key, count in seams.most_common():
        print(count, key)


main()
