"""Native multi-body, sweep, loft and edge-chain controls.

Builds one-variable parts through the Fusion API and exports them to
Controls/ for decoding: combine variants, splits, body patterns, a second
revolved body, line-and-arc sweeps, lofts between parallel profiles and
fillets or chamfers on horizontal and curved edges. CaptureSweeps.py runs
only the rectangle sweeps along a bent path.
Evidence for Kit authoring, not Kit acceptance.
Run only through RunLocked.mjs. Every document opened here is closed.
"""

import hashlib
import json
import math
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent / "Controls"
root.mkdir(exist_ok=True)
app = adsk.core.Application.get()
original = app.activeDocument
report = {"fusion_version": app.version, "documents_before": app.documents.count, "scope": "Native multi-body, sweep, loft and edge-chain controls created through the Fusion API and exported locally; evidence for Kit feature authoring, not Kit acceptance", "controls": []}
FO = adsk.fusion.FeatureOperations


def checkpoint():
    (root / globals().get("REPORT", "CaptureBodies.json")).write_text(json.dumps(report, indent=2).replace(str(Path(__file__).resolve().parents[4]) + "/", "").replace(str(Path.home()), "~") + "\n")


def vi(text):
    return adsk.core.ValueInput.createByString(text)


def pt(x, y, z=0.0):
    return adsk.core.Point3D.create(x, y, z)


def coll(*items):
    value = adsk.core.ObjectCollection.create()
    for item in items:
        value.add(item)
    return value


def block(comp, x0=0.0, y0=0.0, x1=4.0, y1=3.0, height="20 mm", name="Base"):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = name + " sketch"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(x0, y0), pt(x1, y1))
    ext = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi(height), FO.NewBodyFeatureOperation)
    ext.name = name + " extrude"
    return ext


def post(comp, cx=4.0, cy=3.0, r=1.0, height="20 mm", name="Post"):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = name + " sketch"
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(cx, cy), r)
    ext = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi(height), FO.NewBodyFeatureOperation)
    ext.name = name + " extrude"
    return ext


def combine(comp, operation, keep):
    target = block(comp).bodies.item(0)
    tool = post(comp).bodies.item(0)
    feats = comp.features.combineFeatures
    inp = feats.createInput(target, coll(tool))
    inp.operation = operation
    inp.isKeepToolBodies = keep
    c = feats.add(inp)
    c.name = "Body combine"


def offset_plane(comp, base, amount, name):
    planes = comp.constructionPlanes
    pi = planes.createInput()
    pi.setByOffset(base, vi(amount))
    plane = planes.add(pi)
    plane.name = name
    return plane


def split(comp, base, amount):
    body = block(comp).bodies.item(0)
    plane = offset_plane(comp, base, amount, "Split plane")
    feats = comp.features.splitBodyFeatures
    s = feats.add(feats.createInput(body, plane, True))
    s.name = "Body split"


def c_split_xz(comp, design):
    split(comp, comp.xZConstructionPlane, "10 mm")


def c_split_xy(comp, design):
    split(comp, comp.xYConstructionPlane, "8 mm")


def c_body_rect(comp, design):
    body = block(comp, 0, 0, 1, 1, "10 mm", "Cube").bodies.item(0)
    feats = comp.features.rectangularPatternFeatures
    inp = feats.createInput(coll(body), comp.xConstructionAxis, adsk.core.ValueInput.createByReal(3), vi("15 mm"), adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
    inp.setDirectionTwo(comp.yConstructionAxis, adsk.core.ValueInput.createByReal(2), vi("20 mm"))
    p = feats.add(inp)
    p.name = "Cube grid"


def c_body_circ(comp, design):
    body = block(comp, 2, -0.5, 3, 0.5, "10 mm", "Cube").bodies.item(0)
    feats = comp.features.circularPatternFeatures
    inp = feats.createInput(coll(body), comp.zConstructionAxis)
    inp.quantity = adsk.core.ValueInput.createByReal(4)
    inp.totalAngle = vi("360 deg")
    inp.isSymmetric = False
    p = feats.add(inp)
    p.name = "Cube ring"


def c_revolve_body(comp, design):
    block(comp)
    sk = comp.sketches.add(comp.xZConstructionPlane)
    sk.name = "Ring sketch"
    corners = [sk.modelToSketchSpace(pt(x, 0, z)) for x, z in ((6, 0), (8, 0), (8, 1), (6, 1))]
    lines = sk.sketchCurves.sketchLines
    for index in range(4):
        lines.addByTwoPoints(corners[index], corners[(index + 1) % 4])
    feats = comp.features.revolveFeatures
    inp = feats.createInput(sk.profiles.item(0), comp.zConstructionAxis, FO.NewBodyFeatureOperation)
    inp.setAngleExtent(False, vi("360 deg"))
    r = feats.add(inp)
    r.name = "Ring revolve"


def c_sweep_line_arc(comp, design):
    profile = comp.sketches.add(comp.xYConstructionPlane)
    profile.name = "Sweep profile"
    profile.sketchCurves.sketchCircles.addByCenterRadius(pt(0, 0), 0.5)
    sk = comp.sketches.add(comp.xZConstructionPlane)
    sk.name = "Sweep path"
    start = sk.modelToSketchSpace(pt(0, 0, 0))
    bend = sk.modelToSketchSpace(pt(0, 0, 2))
    line = sk.sketchCurves.sketchLines.addByTwoPoints(start, bend)
    arc = sk.sketchCurves.sketchArcs.addByCenterStartSweep(sk.modelToSketchSpace(pt(3, 0, 2)), line.endSketchPoint, -math.pi / 2)
    if arc.endSketchPoint.worldGeometry.z < 2.0:
        arc.deleteMe()
        arc = sk.sketchCurves.sketchArcs.addByCenterStartSweep(sk.modelToSketchSpace(pt(3, 0, 2)), line.endSketchPoint, math.pi / 2)
    path = comp.features.createPath(coll(line, arc), False)
    inp = comp.features.sweepFeatures.createInput(profile.profiles.item(0), path, FO.NewBodyFeatureOperation)
    s = comp.features.sweepFeatures.add(inp)
    s.name = "Bend sweep"


def sweep_bend(comp, hooked):
    profile = comp.sketches.add(comp.xZConstructionPlane)
    profile.name = "Sweep profile"
    corners = [profile.modelToSketchSpace(pt(x, 0, z)) for x, z in ((-0.5, 0), (0.5, 0), (0.5, 1), (-0.5, 1))]
    lines = profile.sketchCurves.sketchLines
    for index in range(4):
        lines.addByTwoPoints(corners[index], corners[(index + 1) % 4])
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "Sweep path"
    line = sk.sketchCurves.sketchLines.addByTwoPoints(pt(0, 0), pt(0, 2))
    arc = sk.sketchCurves.sketchArcs.addByCenterStartSweep(pt(-3, 2), line.endSketchPoint, math.pi / 2)
    curves = [line, arc]
    if hooked:
        curves.append(sk.sketchCurves.sketchLines.addByTwoPoints(arc.endSketchPoint, pt(-5, 5)))
    path = comp.features.createPath(coll(*curves), False)
    inp = comp.features.sweepFeatures.createInput(profile.profiles.item(0), path, FO.NewBodyFeatureOperation)
    s = comp.features.sweepFeatures.add(inp)
    s.name = "Bend sweep"


def loft(comp, lower_build, upper_build, name):
    lower = comp.sketches.add(comp.xYConstructionPlane)
    lower.name = "Loft base"
    lower_build(lower)
    plane = offset_plane(comp, comp.xYConstructionPlane, "30 mm", "Loft plane")
    upper = comp.sketches.add(plane)
    upper.name = "Loft top"
    upper_build(upper)
    inp = comp.features.loftFeatures.createInput(FO.NewBodyFeatureOperation)
    inp.loftSections.add(lower.profiles.item(0))
    inp.loftSections.add(upper.profiles.item(0))
    l = comp.features.loftFeatures.add(inp)
    l.name = name


def c_loft_rects(comp, design):
    loft(comp, lambda sk: sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(0, 0), pt(4, 3)), lambda sk: sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(1, 1), pt(3, 2)), "Block loft")


def c_loft_circles(comp, design):
    loft(comp, lambda sk: sk.sketchCurves.sketchCircles.addByCenterRadius(pt(0, 0), 1.0), lambda sk: sk.sketchCurves.sketchCircles.addByCenterRadius(pt(0, 0), 0.5), "Cone loft")


def top_edge(body, y):
    for edge in body.edges:
        s, e = edge.startVertex.geometry, edge.endVertex.geometry
        if abs(s.z - 2) < 1e-6 and abs(e.z - 2) < 1e-6 and abs(s.y - y) < 1e-6 and abs(e.y - y) < 1e-6:
            return edge
    raise RuntimeError("Top edge not found")


def c_fillet_top(comp, design):
    body = block(comp).bodies.item(0)
    feats = comp.features.filletFeatures
    inp = feats.createInput()
    inp.edgeSetInputs.addConstantRadiusEdgeSet(coll(top_edge(body, 0)), vi("3 mm"), True)
    f = feats.add(inp)
    f.name = "Top round"


def c_chamfer_top(comp, design):
    body = block(comp).bodies.item(0)
    feats = comp.features.chamferFeatures
    inp = feats.createInput2()
    inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(coll(top_edge(body, 0)), vi("3 mm"), True)
    f = feats.add(inp)
    f.name = "Top bevel"


def vertical_edges(body):
    found = []
    for edge in body.edges:
        s, e = edge.startVertex.geometry, edge.endVertex.geometry
        if abs(s.x - e.x) < 1e-6 and abs(s.y - e.y) < 1e-6:
            found.append(edge)
    return found


def c_fillet_chain(comp, design):
    body = block(comp).bodies.item(0)
    feats = comp.features.filletFeatures
    inp = feats.createInput()
    inp.edgeSetInputs.addConstantRadiusEdgeSet(coll(*vertical_edges(body)), vi("5 mm"), True)
    corners = feats.add(inp)
    corners.name = "Corner rounds"
    body = comp.bRepBodies.item(0)
    inp = feats.createInput()
    inp.edgeSetInputs.addConstantRadiusEdgeSet(coll(top_edge(body, 0)), vi("2 mm"), True)
    f = feats.add(inp)
    f.name = "Top chain"


def c_fillet_rim(comp, design):
    body = post(comp, 0, 0, 1.0, "20 mm", "Disc").bodies.item(0)
    rim = [e for e in body.edges if e.geometry.curveType == adsk.core.Curve3DTypes.Circle3DCurveType and abs(e.geometry.center.z - 2) < 1e-6]
    feats = comp.features.filletFeatures
    inp = feats.createInput()
    inp.edgeSetInputs.addConstantRadiusEdgeSet(coll(*rim), vi("3 mm"), True)
    f = feats.add(inp)
    f.name = "Rim round"


controls = [
    ("CombineCut", lambda comp, design: combine(comp, FO.CutFeatureOperation, False)),
    ("CombineIntersect", lambda comp, design: combine(comp, FO.IntersectFeatureOperation, False)),
    ("CombineKeep", lambda comp, design: combine(comp, FO.JoinFeatureOperation, True)),
    ("SplitXZ", c_split_xz),
    ("SplitXY", c_split_xy),
    ("BodyRectPattern", c_body_rect),
    ("BodyCircPattern", c_body_circ),
    ("RevolveBody", c_revolve_body),
    ("SweepLineArc", c_sweep_line_arc),
    ("SweepBend", lambda comp, design: sweep_bend(comp, False)),
    ("SweepHook", lambda comp, design: sweep_bend(comp, True)),
    ("LoftRects", c_loft_rects),
    ("LoftCircles", c_loft_circles),
    ("FilletTop", c_fillet_top),
    ("ChamferTop", c_chamfer_top),
    ("FilletChain", c_fillet_chain),
    ("FilletRim", c_fillet_rim),
]


def observe(design):
    comp = design.rootComponent
    bodies = []
    for b in comp.bRepBodies:
        bb = b.boundingBox
        props = b.physicalProperties
        bodies.append({"name": b.name, "solid": b.isSolid, "volume_cm3": b.volume, "area_cm2": b.area, "faces": b.faces.count, "edges": b.edges.count, "vertices": b.vertices.count, "min_cm": bb.minPoint.asArray(), "max_cm": bb.maxPoint.asArray(), "center_cm": props.centerOfMass.asArray(), "surface_types": sorted(f.geometry.surfaceType for f in b.faces)})
    timeline = [{"name": i.name, "health": i.healthState, "message": i.errorOrWarningMessage} for i in design.timeline]
    params = []
    for p in design.allParameters:
        role = None
        owner = None
        try:
            model = adsk.fusion.ModelParameter.cast(p)
            role = model.role if model else None
            owner = p.createdBy.name if p.createdBy else None
        except Exception:
            role = None
        params.append({"name": p.name, "expression": p.expression, "value": p.value, "unit": p.unit, "role": role, "owner": owner})
    return {"timeline": timeline, "parameters": params, "bodies": bodies, "profiles": [s.profiles.count for s in comp.sketches]}


try:
    for name, build in controls:
        if globals().get("ONLY") and name not in globals()["ONLY"]:
            continue
        entry = {"name": name, "status": "started"}
        report["controls"].append(entry)
        doc = None
        try:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            build(design.rootComponent, design)
            if not design.computeAll():
                raise RuntimeError("Native control did not recompute")
            entry["observed"] = observe(design)
            path = root / (name + ".f3d")
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):
                raise RuntimeError("Native control export failed")
            entry["file"] = path.name
            entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            entry["bytes"] = path.stat().st_size
            entry["status"] = "captured"
        except Exception:
            entry["status"] = "failed"
            entry["traceback"] = traceback.format_exc()
        finally:
            if doc is not None:
                doc.close(False)
            checkpoint()
    report["status"] = "captured"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
finally:
    if original is not None and original.isValid:
        original.activate()
    report["documents_after"] = app.documents.count
    checkpoint()
