"""Native controls for boundary booleans, round extents and edge feature variants.

Builds one-variable parts through the Fusion API and exports them to
Controls/ for decoding. Evidence for Kit authoring, not Kit acceptance.
Run only through RunLocked.mjs. Every document opened here is closed.
"""

import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent / "Controls"
root.mkdir(exist_ok=True)
app = adsk.core.Application.get()
original = app.activeDocument
report = {"fusion_version": app.version, "documents_before": app.documents.count, "scope": "Native boundary boolean, round extent, edge feature, offset face and feature pattern controls created through the Fusion API and exported locally; evidence for Kit feature authoring, not Kit acceptance", "controls": []}
FO = adsk.fusion.FeatureOperations


def checkpoint():
    (root / globals().get("REPORT", "CaptureFamilies.json")).write_text(json.dumps(report, indent=2).replace(str(Path(__file__).resolve().parents[4]) + "/", "").replace(str(Path.home()), "~") + "\n")


def vi(text):
    return adsk.core.ValueInput.createByString(text)


def pt(x, y, z=0.0):
    return adsk.core.Point3D.create(x, y, z)


def coll(*items):
    value = adsk.core.ObjectCollection.create()
    for item in items:
        value.add(item)
    return value


def base(comp, height="20 mm"):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "Base sketch"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(0, 0), pt(4, 3))
    ext = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi(height), FO.NewBodyFeatureOperation)
    ext.name = "Base extrude"
    return ext


def circle_tool(comp, cx, cy, r, distance, operation, name):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = name + " sketch"
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(cx, cy), r)
    e = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi(distance), operation)
    e.name = name
    return e


def rect_tool(comp, x0, y0, x1, y1, operation, name):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = name + " sketch"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(x0, y0), pt(x1, y1))
    e = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi("20 mm"), operation)
    e.name = name
    return e


def disc(comp, extent):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "Disc sketch"
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(2, 1.5), 1.0)
    feats = comp.features.extrudeFeatures
    inp = feats.createInput(sk.profiles.item(0), FO.NewBodyFeatureOperation)
    if extent == "symmetric":
        inp.setSymmetricExtent(vi("20 mm"), True)
    elif extent == "two":
        inp.setTwoSidesExtent(adsk.fusion.DistanceExtentDefinition.create(vi("20 mm")), adsk.fusion.DistanceExtentDefinition.create(vi("5 mm")))
    else:
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(vi("20 mm")), adsk.fusion.ExtentDirections.NegativeExtentDirection)
    e = feats.add(inp)
    e.name = "Disc extrude"


def vertical_edge(body, x, y):
    for edge in body.edges:
        s, e = edge.startVertex.geometry, edge.endVertex.geometry
        if abs(s.x - x) < 1e-6 and abs(e.x - x) < 1e-6 and abs(s.y - y) < 1e-6 and abs(e.y - y) < 1e-6:
            return edge
    raise RuntimeError("Vertical edge not found")


def planar_face(body, nx, ny, nz):
    best = None
    for face in body.faces:
        if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            ok, normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
            if normal.x * nx + normal.y * ny + normal.z * nz > 0.999:
                best = face
    return best


def c_fillet_two(comp, design):
    body = base(comp).bodies.item(0)
    feats = comp.features.filletFeatures
    inp = feats.createInput()
    inp.edgeSetInputs.addConstantRadiusEdgeSet(coll(vertical_edge(body, 4, 3), vertical_edge(body, 0, 0)), vi("3 mm"), True)
    f = feats.add(inp)
    f.name = "Corner rounds"


def c_chamfer_two(comp, design):
    body = base(comp).bodies.item(0)
    feats = comp.features.chamferFeatures
    inp = feats.createInput2()
    inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(coll(vertical_edge(body, 4, 3), vertical_edge(body, 0, 0)), vi("3 mm"), True)
    f = feats.add(inp)
    f.name = "Corner bevels"


def c_chamfer_distances(comp, design):
    body = base(comp).bodies.item(0)
    feats = comp.features.chamferFeatures
    inp = feats.createInput2()
    inp.chamferEdgeSets.addTwoDistancesChamferEdgeSet(coll(vertical_edge(body, 4, 3)), vi("3 mm"), vi("2 mm"), False, True)
    f = feats.add(inp)
    f.name = "Corner bevel"


def c_chamfer_angle(comp, design):
    body = base(comp).bodies.item(0)
    feats = comp.features.chamferFeatures
    inp = feats.createInput2()
    inp.chamferEdgeSets.addDistanceAndAngleChamferEdgeSet(coll(vertical_edge(body, 4, 3)), vi("3 mm"), vi("30 deg"), False, True)
    f = feats.add(inp)
    f.name = "Corner bevel"


def c_shell_side(comp, design):
    body = base(comp).bodies.item(0)
    feats = comp.features.shellFeatures
    inp = feats.createInput(coll(planar_face(body, 0, 0, 1), planar_face(body, 0, -1, 0)), False)
    inp.insideThickness = vi("2 mm")
    f = feats.add(inp)
    f.name = "Open shell"


def c_offset_top(comp, design):
    body = base(comp).bodies.item(0)
    feats = comp.features.offsetFacesFeatures
    inp = feats.createInput([planar_face(body, 0, 0, 1)], vi("5 mm"))
    f = feats.add(inp)
    f.name = "Top offset"


def c_offset_side(comp, design):
    body = base(comp).bodies.item(0)
    feats = comp.features.offsetFacesFeatures
    inp = feats.createInput([planar_face(body, 1, 0, 0)], vi("4 mm"))
    f = feats.add(inp)
    f.name = "Side offset"


def c_offset_bore(comp, design):
    base(comp)
    circle_tool(comp, 2, 1.5, 0.5, "20 mm", FO.CutFeatureOperation, "Hole extrude")
    body = comp.bRepBodies.item(0)
    bore = [f for f in body.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType][0]
    feats = comp.features.offsetFacesFeatures
    inp = feats.createInput([bore], vi("1 mm"))
    f = feats.add(inp)
    f.name = "Bore offset"


def c_circ_inside(comp, design):
    base(comp)
    cut = circle_tool(comp, 3.0, 0.8, 0.3, "20 mm", FO.CutFeatureOperation, "Pocket extrude")
    feats = comp.features.circularPatternFeatures
    inp = feats.createInput(coll(cut), comp.zConstructionAxis)
    inp.quantity = adsk.core.ValueInput.createByReal(3)
    inp.totalAngle = vi("40 deg")
    inp.isSymmetric = False
    p = feats.add(inp)
    p.name = "Pocket arc"


def c_construction_set(comp, design):
    body = base(comp).bodies.item(0)
    planes = comp.constructionPlanes
    pi = planes.createInput()
    pi.setByOffset(comp.xYConstructionPlane, vi("15 mm"))
    plane = planes.add(pi)
    plane.name = "Offset plane"
    axes = comp.constructionAxes
    ai = axes.createInput()
    ai.setByEdge(vertical_edge(body, 4, 3))
    axis = axes.add(ai)
    axis.name = "Edge axis"
    points = comp.constructionPoints
    qi = points.createInput()
    qi.setByPoint(body.vertices.item(0))
    point = points.add(qi)
    point.name = "Corner point"


def c_hole_offset(comp, design):
    body = base(comp).bodies.item(0)
    feats = comp.features.holeFeatures
    inp = feats.createSimpleInput(vi("4 mm"))
    inp.setPositionByPoint(planar_face(body, 0, 0, 1), pt(0.8, 0.6, 2.0))
    inp.setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)
    hole = feats.add(inp)
    hole.name = "Offset hole"


def c_hole_notch(comp, design):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "Notch sketch"
    lines = sk.sketchCurves.sketchLines
    lines.addByTwoPoints(pt(0, 0), pt(4, 0))
    lines.addByTwoPoints(pt(4, 0), pt(4, 3))
    lines.addByTwoPoints(pt(4, 3), pt(3, 3))
    sk.sketchCurves.sketchArcs.addByThreePoints(pt(3, 3), pt(2, 2), pt(1, 3))
    lines.addByTwoPoints(pt(1, 3), pt(0, 3))
    lines.addByTwoPoints(pt(0, 3), pt(0, 0))
    comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi("20 mm"), FO.NewBodyFeatureOperation).name = "Notch extrude"
    feats = comp.features.holeFeatures
    inp = feats.createSimpleInput(vi("4 mm"))
    inp.setPositionByPoint(planar_face(comp.bRepBodies.item(0), 0, 0, 1), pt(0.8, 0.6, 2.0))
    inp.setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)
    feats.add(inp).name = "Offset hole"


def c_disc_bore(comp, design):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "Disc sketch"
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(0, 0), 2.0)
    comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi("12 mm"), FO.NewBodyFeatureOperation)
    cut = circle_tool(comp, 1.2, 0, 0.3, "6 mm", FO.CutFeatureOperation, "Pocket extrude")
    feats = comp.features.circularPatternFeatures
    inp = feats.createInput(coll(cut), comp.zConstructionAxis)
    inp.quantity = adsk.core.ValueInput.createByReal(4)
    inp.totalAngle = vi("360 deg")
    inp.isSymmetric = False
    feats.add(inp).name = "Pocket ring"
    holes = comp.features.holeFeatures
    hi = holes.createCounterboreInput(vi("8 mm"), vi("14 mm"), vi("4 mm"))
    hi.setPositionByPoint(planar_face(comp.bRepBodies.item(0), 0, 0, 1), pt(0, 0, 1.2))
    hi.setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)
    holes.add(hi).name = "Center bore"


controls = [
    ("HoleOffset", c_hole_offset),
    ("HoleNotch", c_hole_notch),
    ("DiscBore", c_disc_bore),
    ("EdgeNotch", lambda comp, design: (base(comp), circle_tool(comp, 0, 1.5, 0.5, "20 mm", FO.CutFeatureOperation, "Notch"))),
    ("EdgeBoss", lambda comp, design: (base(comp), circle_tool(comp, 4, 1.5, 0.5, "20 mm", FO.JoinFeatureOperation, "Boss"))),
    ("EdgeCore", lambda comp, design: (base(comp), circle_tool(comp, 4, 1.5, 1.0, "20 mm", FO.IntersectFeatureOperation, "Core"))),
    ("CornerCut", lambda comp, design: (base(comp), rect_tool(comp, 3, 2, 5, 4, FO.CutFeatureOperation, "Corner"))),
    ("SideJoin", lambda comp, design: (base(comp), rect_tool(comp, 4, 0, 5, 3, FO.JoinFeatureOperation, "Side"))),
    ("DiscSymmetric", lambda comp, design: disc(comp, "symmetric")),
    ("DiscTwoSided", lambda comp, design: disc(comp, "two")),
    ("DiscFlip", lambda comp, design: disc(comp, "flip")),
    ("FilletTwoEdges", c_fillet_two),
    ("ChamferTwoEdges", c_chamfer_two),
    ("ChamferTwoDistances", c_chamfer_distances),
    ("ChamferDistanceAngle", c_chamfer_angle),
    ("ShellOpenSide", c_shell_side),
    ("OffsetTop", c_offset_top),
    ("OffsetSide", c_offset_side),
    ("OffsetBore", c_offset_bore),
    ("CircPatternInside", c_circ_inside),
    ("ConstructionSet", c_construction_set),
]


def observe(design):
    comp = design.rootComponent
    bodies = []
    for b in comp.bRepBodies:
        bb = b.boundingBox
        bodies.append({"name": b.name, "solid": b.isSolid, "volume_cm3": b.volume, "area_cm2": b.area, "faces": b.faces.count, "edges": b.edges.count, "vertices": b.vertices.count, "min_cm": bb.minPoint.asArray(), "max_cm": bb.maxPoint.asArray(), "surface_types": sorted(f.geometry.surfaceType for f in b.faces)})
    timeline = [{"name": i.name, "health": i.healthState, "message": i.errorOrWarningMessage} for i in design.timeline]
    params = []
    for p in design.allParameters:
        role = None
        try:
            model = adsk.fusion.ModelParameter.cast(p)
            role = model.role if model else None
        except Exception:
            role = None
        params.append({"name": p.name, "expression": p.expression, "value": p.value, "unit": p.unit, "role": role})
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
