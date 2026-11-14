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
report = {"fusion_version": app.version, "documents_before": app.documents.count, "scope": "Native one-variable feature-family controls created through the Fusion API and exported locally; evidence for Kit feature authoring, not Kit acceptance", "controls": []}
FO = adsk.fusion.FeatureOperations


def checkpoint():
    (root / "Capture.json").write_text(json.dumps(report, indent=2).replace(str(Path(__file__).resolve().parents[4]) + "/", "").replace(str(Path.home()), "~") + "\n")


def vi(text):
    return adsk.core.ValueInput.createByString(text)


def pt(x, y, z=0.0):
    return adsk.core.Point3D.create(x, y, z)


def coll(*items):
    value = adsk.core.ObjectCollection.create()
    for item in items:
        value.add(item)
    return value


def base(comp, height="20 mm", name="Base"):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = name + " sketch"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(0, 0), pt(4, 3))
    ext = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi(height), FO.NewBodyFeatureOperation)
    ext.name = name + " extrude"
    return ext


def circle_sketch(comp, plane, cx, cy, r, name):
    sk = comp.sketches.add(plane)
    sk.name = name
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(cx, cy), r)
    return sk


def face_where(body, test):
    return [f for f in body.faces if test(f)]


def planar_normal(face):
    ok, normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
    return normal


def top_face(body):
    best = None
    for face in body.faces:
        if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            n = planar_normal(face)
            if n.z > 0.999 and (best is None or face.pointOnFace.z > best.pointOnFace.z):
                best = face
    return best


def bottom_face(body):
    for face in body.faces:
        if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            n = planar_normal(face)
            if n.z < -0.999 and abs(face.pointOnFace.z) < 1e-6:
                return face
    return None


def side_faces(body):
    return [f for f in body.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType and abs(planar_normal(f).z) < 1e-6]


def vertical_edge(body, x, y):
    for edge in body.edges:
        s, e = edge.startVertex.geometry, edge.endVertex.geometry
        if abs(s.x - x) < 1e-6 and abs(e.x - x) < 1e-6 and abs(s.y - y) < 1e-6 and abs(e.y - y) < 1e-6:
            return edge
    raise RuntimeError("Vertical edge not found")


def observe(design):
    comp = design.rootComponent
    bodies = []
    for b in comp.bRepBodies:
        bb = b.boundingBox
        bodies.append({"name": b.name, "solid": b.isSolid, "volume_cm3": b.volume, "area_cm2": b.area, "faces": b.faces.count, "edges": b.edges.count, "vertices": b.vertices.count, "min_cm": bb.minPoint.asArray(), "max_cm": bb.maxPoint.asArray(), "surface_types": sorted(f.geometry.surfaceType for f in b.faces)})
    timeline = []
    for item in design.timeline:
        entity = item.entity
        timeline.append({"name": item.name, "object_type": entity.objectType if entity else None, "health": item.healthState, "message": item.errorOrWarningMessage})
    params = []
    for p in design.allParameters:
        owner = None
        try:
            owner = p.createdBy.objectType if p.createdBy else None
        except Exception:
            owner = None
        params.append({"name": p.name, "expression": p.expression, "value": p.value, "unit": p.unit, "owner": owner, "role": getattr(p, "role", None)})
    return {"timeline": timeline, "parameters": params, "bodies": bodies, "sketches": [{"name": s.name, "profiles": s.profiles.count, "curves": s.sketchCurves.count, "points": s.sketchPoints.count, "constraints": [c.objectType for c in s.geometricConstraints], "dimensions": [{"type": d.objectType, "parameter": d.parameter.name, "expression": d.parameter.expression} for d in s.sketchDimensions]} for s in comp.sketches], "planes": comp.constructionPlanes.count, "axes": comp.constructionAxes.count, "points": comp.constructionPoints.count}


def c_extrude_new(comp, design):
    base(comp)


def c_extrude_tall(comp, design):
    base(comp, "26 mm")


def c_extrude_symmetric(comp, design):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "Base sketch"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(0, 0), pt(4, 3))
    ext = comp.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), FO.NewBodyFeatureOperation)
    inp.setSymmetricExtent(vi("20 mm"), True)
    e = ext.add(inp)
    e.name = "Base extrude"


def c_extrude_join(comp, design):
    base(comp)
    sk = circle_sketch(comp, comp.xYConstructionPlane, 2, 1.5, 0.5, "Boss sketch")
    e = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi("30 mm"), FO.JoinFeatureOperation)
    e.name = "Boss extrude"


def c_extrude_cut(comp, design):
    base(comp)
    sk = circle_sketch(comp, comp.xYConstructionPlane, 2, 1.5, 0.5, "Hole sketch")
    e = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi("20 mm"), FO.CutFeatureOperation)
    e.name = "Hole extrude"


def c_extrude_cut_radius(comp, design):
    base(comp)
    sk = circle_sketch(comp, comp.xYConstructionPlane, 2, 1.5, 0.7, "Hole sketch")
    e = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi("20 mm"), FO.CutFeatureOperation)
    e.name = "Hole extrude"


def c_extrude_intersect(comp, design):
    base(comp)
    sk = circle_sketch(comp, comp.xYConstructionPlane, 2, 1.5, 1.0, "Core sketch")
    e = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi("20 mm"), FO.IntersectFeatureOperation)
    e.name = "Core extrude"


def c_extrude_second_body(comp, design):
    base(comp)
    sk = circle_sketch(comp, comp.xYConstructionPlane, 6, 1.5, 0.5, "Post sketch")
    e = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi("20 mm"), FO.NewBodyFeatureOperation)
    e.name = "Post extrude"


def c_extrude_to_object(comp, design):
    ext = base(comp)
    body = ext.bodies.item(0)
    planes = comp.constructionPlanes
    pi = planes.createInput()
    pi.setByOffset(comp.xYConstructionPlane, vi("50 mm"))
    plane = planes.add(pi)
    plane.name = "Upper plane"
    sk = circle_sketch(comp, plane, 2, 1.5, 0.5, "Drop sketch")
    face = top_face(body)
    inp = comp.features.extrudeFeatures.createInput(sk.profiles.item(0), FO.JoinFeatureOperation)
    inp.setOneSideExtent(adsk.fusion.ToEntityExtentDefinition.create(face, False), adsk.fusion.ExtentDirections.NegativeExtentDirection)
    e = comp.features.extrudeFeatures.add(inp)
    e.name = "Drop extrude"


def revolve_profile(comp):
    sk = comp.sketches.add(comp.xZConstructionPlane)
    sk.name = "Revolve sketch"
    corners = [sk.modelToSketchSpace(pt(x, 0, z)) for x, z in ((1, 0), (2, 0), (2, 3), (1, 3))]
    lines = sk.sketchCurves.sketchLines
    for index in range(4):
        lines.addByTwoPoints(corners[index], corners[(index + 1) % 4])
    return sk


def c_revolve_full(comp, design):
    sk = revolve_profile(comp)
    inp = comp.features.revolveFeatures.createInput(sk.profiles.item(0), comp.zConstructionAxis, FO.NewBodyFeatureOperation)
    inp.setAngleExtent(False, vi("360 deg"))
    r = comp.features.revolveFeatures.add(inp)
    r.name = "Tube revolve"


def c_revolve_half(comp, design):
    sk = revolve_profile(comp)
    inp = comp.features.revolveFeatures.createInput(sk.profiles.item(0), comp.zConstructionAxis, FO.NewBodyFeatureOperation)
    inp.setAngleExtent(False, vi("180 deg"))
    r = comp.features.revolveFeatures.add(inp)
    r.name = "Tube revolve"


def fillet(comp, edge, radius):
    feats = comp.features.filletFeatures
    inp = feats.createInput()
    try:
        inp.edgeSetInputs.addConstantRadiusEdgeSet(coll(edge), vi(radius), True)
    except AttributeError:
        inp.addConstantRadiusEdgeSet(coll(edge), vi(radius), True)
    f = feats.add(inp)
    f.name = "Corner fillet"
    return f


def c_fillet(comp, design):
    body = base(comp).bodies.item(0)
    fillet(comp, vertical_edge(body, 4, 3), "3 mm")


def c_fillet_radius(comp, design):
    body = base(comp).bodies.item(0)
    fillet(comp, vertical_edge(body, 4, 3), "5 mm")


def chamfer(comp, edge, distance):
    feats = comp.features.chamferFeatures
    try:
        inp = feats.createInput2()
        inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(coll(edge), vi(distance), True)
    except AttributeError:
        inp = feats.createInput(coll(edge), True)
        inp.setToEqualDistance(vi(distance))
    c = feats.add(inp)
    c.name = "Corner chamfer"
    return c


def c_chamfer(comp, design):
    body = base(comp).bodies.item(0)
    chamfer(comp, vertical_edge(body, 4, 3), "3 mm")


def c_chamfer_distance(comp, design):
    body = base(comp).bodies.item(0)
    chamfer(comp, vertical_edge(body, 4, 3), "5 mm")


def shell(comp, body, thickness):
    feats = comp.features.shellFeatures
    inp = feats.createInput(coll(top_face(body)), False)
    inp.insideThickness = vi(thickness)
    s = feats.add(inp)
    s.name = "Open shell"
    return s


def c_shell(comp, design):
    body = base(comp).bodies.item(0)
    shell(comp, body, "2 mm")


def c_shell_thickness(comp, design):
    body = base(comp).bodies.item(0)
    shell(comp, body, "3 mm")


def hole(comp, body, diameter, depth):
    feats = comp.features.holeFeatures
    inp = feats.createSimpleInput(vi(diameter))
    inp.setPositionByPoint(top_face(body), pt(2, 1.5, 2))
    inp.setDistanceExtent(vi(depth))
    h = feats.add(inp)
    h.name = "Top hole"
    return h


def c_hole(comp, design):
    body = base(comp).bodies.item(0)
    hole(comp, body, "8 mm", "10 mm")


def c_hole_diameter(comp, design):
    body = base(comp).bodies.item(0)
    hole(comp, body, "6 mm", "10 mm")


def small_cut(comp):
    sk = circle_sketch(comp, comp.xYConstructionPlane, 0.8, 0.8, 0.3, "Pocket sketch")
    e = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi("20 mm"), FO.CutFeatureOperation)
    e.name = "Pocket extrude"
    return e


def rect_pattern(comp, cut, count):
    feats = comp.features.rectangularPatternFeatures
    inp = feats.createInput(coll(cut), comp.xConstructionAxis, adsk.core.ValueInput.createByReal(count), vi("12 mm"), adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
    inp.setDirectionTwo(comp.yConstructionAxis, adsk.core.ValueInput.createByReal(2), vi("14 mm"))
    p = feats.add(inp)
    p.name = "Pocket grid"
    return p


def c_rect_pattern(comp, design):
    base(comp)
    rect_pattern(comp, small_cut(comp), 3)


def c_rect_pattern_count(comp, design):
    base(comp)
    rect_pattern(comp, small_cut(comp), 2)


def circ_pattern(comp, body, count):
    feats = comp.features.circularPatternFeatures
    inp = feats.createInput(coll(body), comp.zConstructionAxis)
    inp.quantity = adsk.core.ValueInput.createByReal(count)
    inp.totalAngle = vi("360 deg")
    inp.isSymmetric = False
    p = feats.add(inp)
    p.name = "Body ring"
    return p


def c_circ_pattern(comp, design):
    body = base(comp).bodies.item(0)
    circ_pattern(comp, body, 4)


def c_circ_pattern_count(comp, design):
    body = base(comp).bodies.item(0)
    circ_pattern(comp, body, 3)


def c_feature_circ_pattern(comp, design):
    base(comp)
    cut = small_cut(comp)
    feats = comp.features.circularPatternFeatures
    inp = feats.createInput(coll(cut), comp.zConstructionAxis)
    inp.quantity = adsk.core.ValueInput.createByReal(2)
    inp.totalAngle = vi("40 deg")
    inp.isSymmetric = False
    p = feats.add(inp)
    p.name = "Pocket arc"


def c_mirror_body(comp, design):
    body = base(comp).bodies.item(0)
    feats = comp.features.mirrorFeatures
    inp = feats.createInput(coll(body), comp.yZConstructionPlane)
    m = feats.add(inp)
    m.name = "Body mirror"


def c_mirror_feature(comp, design):
    base(comp)
    cut = small_cut(comp)
    planes = comp.constructionPlanes
    pi = planes.createInput()
    pi.setByOffset(comp.yZConstructionPlane, vi("20 mm"))
    plane = planes.add(pi)
    plane.name = "Mid plane"
    feats = comp.features.mirrorFeatures
    inp = feats.createInput(coll(cut), plane)
    m = feats.add(inp)
    m.name = "Pocket mirror"


def c_combine(comp, design):
    body = base(comp).bodies.item(0)
    sk = circle_sketch(comp, comp.xYConstructionPlane, 4, 3, 1.0, "Post sketch")
    post = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), vi("20 mm"), FO.NewBodyFeatureOperation)
    post.name = "Post extrude"
    feats = comp.features.combineFeatures
    inp = feats.createInput(body, coll(post.bodies.item(0)))
    inp.operation = FO.JoinFeatureOperation
    c = feats.add(inp)
    c.name = "Body combine"


def c_sweep(comp, design):
    profile = circle_sketch(comp, comp.xYConstructionPlane, 0, 0, 0.5, "Sweep profile")
    sk = comp.sketches.add(comp.xZConstructionPlane)
    sk.name = "Sweep path"
    arc = sk.sketchCurves.sketchArcs.addByCenterStartSweep(sk.modelToSketchSpace(pt(3, 0, 0)), sk.modelToSketchSpace(pt(0, 0, 0)), math.pi / 2)
    path = comp.features.createPath(arc)
    inp = comp.features.sweepFeatures.createInput(profile.profiles.item(0), path, FO.NewBodyFeatureOperation)
    s = comp.features.sweepFeatures.add(inp)
    s.name = "Arc sweep"


def c_loft(comp, design):
    lower = circle_sketch(comp, comp.xYConstructionPlane, 0, 0, 1.0, "Loft base")
    planes = comp.constructionPlanes
    pi = planes.createInput()
    pi.setByOffset(comp.xYConstructionPlane, vi("30 mm"))
    plane = planes.add(pi)
    plane.name = "Loft plane"
    upper = comp.sketches.add(plane)
    upper.name = "Loft top"
    upper.sketchCurves.sketchLines.addTwoPointRectangle(pt(-0.5, -0.5), pt(0.5, 0.5))
    inp = comp.features.loftFeatures.createInput(FO.NewBodyFeatureOperation)
    inp.loftSections.add(lower.profiles.item(0))
    inp.loftSections.add(upper.profiles.item(0))
    l = comp.features.loftFeatures.add(inp)
    l.name = "Round to square"


def c_draft(comp, design):
    body = base(comp).bodies.item(0)
    feats = comp.features.draftFeatures
    inp = feats.createInput(side_faces(body), bottom_face(body), True)
    inp.setSingleAngle(False, vi("5 deg"))
    d = feats.add(inp)
    d.name = "Side draft"


def c_split_body(comp, design):
    body = base(comp).bodies.item(0)
    planes = comp.constructionPlanes
    pi = planes.createInput()
    pi.setByOffset(comp.yZConstructionPlane, vi("20 mm"))
    plane = planes.add(pi)
    plane.name = "Split plane"
    feats = comp.features.splitBodyFeatures
    inp = feats.createInput(body, plane, True)
    s = feats.add(inp)
    s.name = "Body split"


def c_move(comp, design):
    body = base(comp).bodies.item(0)
    feats = comp.features.moveFeatures
    matrix = adsk.core.Matrix3D.create()
    matrix.translation = adsk.core.Vector3D.create(1, 0, 0)
    inp = feats.createInput(coll(body), matrix)
    m = feats.add(inp)
    m.name = "Body move"


def c_copy(comp, design):
    body = base(comp).bodies.item(0)
    comp.features.copyPasteBodies.add(body)


def c_offset_face(comp, design):
    body = base(comp).bodies.item(0)
    feats = comp.features.offsetFacesFeatures
    inp = feats.createInput(coll(top_face(body)), vi("5 mm"))
    o = feats.add(inp)
    o.name = "Top offset"


def c_construction(comp, design):
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
    pinp = points.createInput()
    pinp.setByPoint(vertical_edge(body, 4, 3).startVertex)
    point = points.add(pinp)
    point.name = "Corner point"


def c_offset_plane(comp, design):
    planes = comp.constructionPlanes
    pi = planes.createInput()
    pi.setByOffset(comp.xYConstructionPlane, vi("15 mm"))
    plane = planes.add(pi)
    plane.name = "Offset plane"


def c_sketch_entities(comp, design):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "Entity sketch"
    lines = sk.sketchCurves.sketchLines
    line = lines.addByTwoPoints(pt(0, 0), pt(3, 0))
    arc = sk.sketchCurves.sketchArcs.addByCenterStartSweep(pt(3, 1), line.endSketchPoint, math.pi)
    closing = lines.addByTwoPoints(arc.endSketchPoint, line.startSketchPoint)
    spline_points = coll(pt(0, 3), pt(1, 4), pt(2, 3.5), pt(3, 4.5))
    sk.sketchCurves.sketchFittedSplines.add(spline_points)
    sk.sketchPoints.add(pt(5, 5))
    sk.geometricConstraints.addHorizontal(line)
    sk.geometricConstraints.addTangent(line, arc)
    sk.sketchDimensions.addDistanceDimension(line.startSketchPoint, line.endSketchPoint, adsk.fusion.DimensionOrientations.AlignedDimensionOrientation, pt(1.5, -0.5))
    sk.sketchDimensions.addRadialDimension(arc, pt(4.5, 1.5))


def c_multi_feature(comp, design):
    body = base(comp).bodies.item(0)
    fillet(comp, vertical_edge(body, 4, 3), "3 mm")
    shell(comp, body, "2 mm")
    cut = small_cut(comp)
    rect_pattern(comp, cut, 2)
    feats = comp.features.mirrorFeatures
    inp = feats.createInput(coll(comp.bRepBodies.item(0)), comp.yZConstructionPlane)
    m = feats.add(inp)
    m.name = "Part mirror"


controls = [
    ("ExtrudeNew", c_extrude_new), ("ExtrudeTall", c_extrude_tall), ("ExtrudeSymmetric", c_extrude_symmetric),
    ("ExtrudeJoin", c_extrude_join), ("ExtrudeCut", c_extrude_cut), ("ExtrudeCutRadius", c_extrude_cut_radius),
    ("ExtrudeIntersect", c_extrude_intersect), ("ExtrudeSecondBody", c_extrude_second_body), ("ExtrudeToObject", c_extrude_to_object),
    ("RevolveFull", c_revolve_full), ("RevolveHalf", c_revolve_half),
    ("Fillet", c_fillet), ("FilletRadius", c_fillet_radius), ("Chamfer", c_chamfer), ("ChamferDistance", c_chamfer_distance),
    ("Shell", c_shell), ("ShellThickness", c_shell_thickness), ("Hole", c_hole), ("HoleDiameter", c_hole_diameter),
    ("RectPattern", c_rect_pattern), ("RectPatternCount", c_rect_pattern_count), ("CircPattern", c_circ_pattern), ("CircPatternCount", c_circ_pattern_count),
    ("FeatureCircPattern", c_feature_circ_pattern), ("MirrorBody", c_mirror_body), ("MirrorFeature", c_mirror_feature), ("Combine", c_combine),
    ("Sweep", c_sweep), ("Loft", c_loft), ("Draft", c_draft), ("SplitBody", c_split_body), ("MoveBody", c_move), ("CopyBody", c_copy),
    ("OffsetFace", c_offset_face), ("Construction", c_construction), ("OffsetPlane", c_offset_plane), ("SketchEntities", c_sketch_entities),
    ("MultiFeature", c_multi_feature),
]

try:
    for name, build in controls:
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
