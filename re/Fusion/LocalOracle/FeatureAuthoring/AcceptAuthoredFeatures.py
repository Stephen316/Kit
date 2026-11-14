"""Native acceptance of Kit-authored feature documents.

For every case in Authored/Manifest.json this script:
1. builds the same part natively through the Fusion API as the control;
2. opens the Kit document and observes it before any recompute;
3. walks every timeline rollback marker and compares with the control;
4. runs computeAll and compares again;
5. applies the driving parameter edits to both and compares;
6. exports the edited Kit document, reopens it and compares again.

Run only through RunLocked.mjs. Every document opened here is closed.
Suite wrappers (for example AcceptExtrudes.py) pass SUITE and CASES through
runpy init_globals; the report then goes to NativeAcceptance<SUITE>.json.
"""

import hashlib
import json
from math import isclose, radians
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent / "Authored"
suite = globals().get("SUITE", "")
selected = globals().get("CASES")
manifest = json.loads((root / "Manifest.json").read_text())
if selected is not None:
    manifest = {name: manifest[name] for name in selected}
app = adsk.core.Application.get()
original = app.activeDocument
FO = adsk.fusion.FeatureOperations
HEALTHY = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
report = {
    "fusion_version": app.version,
    "documents_before": app.documents.count,
    "suite": suite or "FilletChamferShell",
    "scope": "Kit-authored part feature documents compared with same-script native API controls: open without recompute, every rollback marker, computeAll, driving parameter edits, export and reopen",
    "cases": [],
}
open_docs = []


def checkpoint():
    (root / ("NativeAcceptance" + suite + ".json")).write_text(json.dumps(report, indent=2).replace(str(Path(__file__).resolve().parents[4]) + "/", "").replace(str(Path.home()), "~") + "\n")


def vi(text):
    return adsk.core.ValueInput.createByString(text)


def pt(x, y, z=0.0):
    return adsk.core.Point3D.create(x, y, z)


def coll(*items):
    value = adsk.core.ObjectCollection.create()
    for item in items:
        value.add(item)
    return value


def vertical_edge(body, x, y):
    for edge in body.edges:
        s, e = edge.startVertex.geometry, edge.endVertex.geometry
        if abs(s.x - x) < 1e-6 and abs(e.x - x) < 1e-6 and abs(s.y - y) < 1e-6 and abs(e.y - y) < 1e-6:
            return edge
    raise RuntimeError("Vertical edge not found")


def corner_vertex(body, x, y):
    found = [v for v in body.vertices if abs(v.geometry.x - x) < 1e-6 and abs(v.geometry.y - y) < 1e-6]
    if not found:
        raise RuntimeError("Corner vertex not found")
    return min(found, key=lambda v: v.geometry.z)


def side_face(body, x, y):
    box = body.boundingBox
    z = (box.minPoint.z + box.maxPoint.z) / 2.0
    found = []
    for face in body.faces:
        if face.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
            continue
        ok, normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
        base_point = face.pointOnFace
        apart = (x - base_point.x) * normal.x + (y - base_point.y) * normal.y + (z - base_point.z) * normal.z
        low, high = face.boundingBox.minPoint, face.boundingBox.maxPoint
        inside = low.x - 1e-6 <= x <= high.x + 1e-6 and low.y - 1e-6 <= y <= high.y + 1e-6
        if abs(apart) < 1e-6 and abs(normal.z) < 1e-6 and inside:
            found.append(face)
    if len(found) != 1:
        raise RuntimeError("Side face not found")
    return found[0]


def draft_faces(body):
    sides, floor = [], None
    for face in body.faces:
        if face.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
            continue
        ok, normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
        if abs(normal.z) < 1e-6:
            sides.append(face)
        elif normal.z < -0.999 and floor is None:
            floor = face
    return sides, floor


def top_face(body):
    best = None
    for face in body.faces:
        if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            ok, normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
            if normal.z > 0.999 and (best is None or face.pointOnFace.z > best.pointOnFace.z):
                best = face
    return best


OPERATIONS = {
    "new": FO.NewBodyFeatureOperation,
    "join": FO.JoinFeatureOperation,
    "cut": FO.CutFeatureOperation,
    "intersect": FO.IntersectFeatureOperation,
}


def draw_profile(sketch, profile):
    points = {}

    def point(xy):
        return points.get((round(xy[0], 9), round(xy[1], 9))) or pt(xy[0], xy[1])

    def remember(*sketch_points):
        for value in sketch_points:
            geometry = value.geometry
            points.setdefault((round(geometry.x, 9), round(geometry.y, 9)), value)

    curves = sketch.sketchCurves
    for curve in profile:
        if curve["kind"] == "line":
            line = curves.sketchLines.addByTwoPoints(point(curve["start_cm"]), point(curve["end_cm"]))
            remember(line.startSketchPoint, line.endSketchPoint)
        elif curve["kind"] == "arc":
            arc = curves.sketchArcs.addByCenterStartSweep(pt(*curve["center_cm"]), point(curve["start_cm"]), curve["sweep_rad"])
            remember(arc.startSketchPoint, arc.endSketchPoint)
        else:
            curves.sketchCircles.addByCenterRadius(pt(*curve["center_cm"]), curve["radius_cm"])


def add_extrude(comp, step):
    sketch = comp.sketches.add(comp.xYConstructionPlane)
    sketch.name = step["sketch"]
    draw_profile(sketch, step["profile"])
    if sketch.profiles.count != 1:
        raise RuntimeError("Control sketch has " + str(sketch.profiles.count) + " profiles")
    feats = comp.features.extrudeFeatures
    inp = feats.createInput(sketch.profiles.item(0), OPERATIONS[step["operation"]])
    distance = adsk.fusion.DistanceExtentDefinition.create(vi(step["amount"]))
    if step["extent"] == "flip":
        inp.setOneSideExtent(distance, adsk.fusion.ExtentDirections.NegativeExtentDirection)
    elif step["extent"] == "symmetric":
        inp.setSymmetricExtent(vi(step["amount"]), True)
    elif step["extent"] == "two":
        inp.setTwoSidesExtent(distance, adsk.fusion.DistanceExtentDefinition.create(vi(step["against"])))
    else:
        inp.setOneSideExtent(distance, adsk.fusion.ExtentDirections.PositiveExtentDirection)
    return feats.add(inp)


def add_revolve(comp, step):
    sketch = comp.sketches.add(comp.xZConstructionPlane)
    sketch.name = step["sketch"]
    inner, outer, lower, upper = step["inner_cm"], step["outer_cm"], step["lower_cm"], step["upper_cm"]
    corners = [sketch.modelToSketchSpace(pt(x, 0, z)) for x, z in ((inner, lower), (outer, lower), (outer, upper), (inner, upper))]
    lines = sketch.sketchCurves.sketchLines
    for index in range(4):
        lines.addByTwoPoints(corners[index], corners[(index + 1) % 4])
    if sketch.profiles.count != 1:
        raise RuntimeError("Control sketch has " + str(sketch.profiles.count) + " profiles")
    feats = comp.features.revolveFeatures
    inp = feats.createInput(sketch.profiles.item(0), comp.zConstructionAxis, OPERATIONS[step["operation"]])
    inp.setAngleExtent(False, vi(step["angle"]))
    return feats.add(inp)


def add_hole(comp, body, step):
    feats = comp.features.holeFeatures
    if step.get("bore_diameter"):
        inp = feats.createCounterboreInput(vi(step["diameter"]), vi(step["bore_diameter"]), vi(step["bore_depth"]))
    elif step.get("sink_diameter"):
        inp = feats.createCountersinkInput(vi(step["diameter"]), vi(step["sink_diameter"]), vi(step["sink_angle"]))
    else:
        inp = feats.createSimpleInput(vi(step["diameter"]))
    face = top_face(body)
    inp.setPositionByPoint(face, pt(step["center_cm"][0], step["center_cm"][1], face.pointOnFace.z))
    if step.get("depth"):
        inp.setDistanceExtent(vi(step["depth"]))
        inp.tipAngle = vi("180 deg")
    else:
        inp.setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)
    return feats.add(inp)


def add_copy(comp, features, step):
    source = features[step["source"]]
    if step["kind"] == "pattern":
        feats = comp.features.rectangularPatternFeatures
        count = adsk.core.ValueInput.createByReal(step["count_u"])
        inp = feats.createInput(coll(source), comp.xConstructionAxis, count, vi(step["spacing_u"]), adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
        inp.setDirectionTwo(comp.yConstructionAxis, adsk.core.ValueInput.createByReal(step["count_v"]), vi(step["spacing_v"]))
        return feats.add(inp)
    if step["kind"] == "circular":
        feats = comp.features.circularPatternFeatures
        inp = feats.createInput(coll(source), comp.zConstructionAxis)
        inp.quantity = adsk.core.ValueInput.createByReal(step["count"])
        inp.totalAngle = vi(step["angle"])
        inp.isSymmetric = False
        return feats.add(inp)
    feats = comp.features.mirrorFeatures
    return feats.add(feats.createInput(coll(source), features[step["plane"]]))


def add_plane(comp, step):
    planes = comp.constructionPlanes
    inp = planes.createInput()
    origin = {"xy": comp.xYConstructionPlane, "yz": comp.yZConstructionPlane, "xz": comp.xZConstructionPlane}[step["base"]]
    inp.setByOffset(origin, vi(step["offset"]))
    return planes.add(inp)


def add_loft(comp, step):
    lower = comp.sketches.add(comp.xYConstructionPlane)
    lower.name = step["lower"]
    draw_profile(lower, step["lower_profile"])
    planes = comp.constructionPlanes
    inp = planes.createInput()
    inp.setByOffset(comp.xYConstructionPlane, vi(step["height"]))
    plane = planes.add(inp)
    plane.name = step["plane"]
    upper = comp.sketches.add(plane)
    upper.name = step["upper"]
    draw_profile(upper, step["upper_profile"])
    if lower.profiles.count != 1 or upper.profiles.count != 1:
        raise RuntimeError("Control loft sketches need one profile each")
    loft_input = comp.features.loftFeatures.createInput(FO.NewBodyFeatureOperation)
    loft_input.loftSections.add(lower.profiles.item(0))
    loft_input.loftSections.add(upper.profiles.item(0))
    return comp.features.loftFeatures.add(loft_input)


def add_sweep(comp, step):
    left, right, lower, upper = step["profile_cm"]
    profile = comp.sketches.add(comp.xZConstructionPlane)
    profile.name = step["profile"]
    corners = [profile.modelToSketchSpace(pt(x, 0, z)) for x, z in ((left, lower), (right, lower), (right, upper), (left, upper))]
    lines = profile.sketchCurves.sketchLines
    for index in range(4):
        lines.addByTwoPoints(corners[index], corners[(index + 1) % 4])
    route = comp.sketches.add(comp.xYConstructionPlane)
    route.name = step["path_name"]
    draw_profile(route, step["path"])
    curves = route.sketchCurves
    if profile.profiles.count != 1 or curves.count != len(step["path"]):
        raise RuntimeError("Control sweep needs one profile and every path curve")
    path = comp.features.createPath(coll(*[curves.item(index) for index in range(curves.count)]), False)
    inp = comp.features.sweepFeatures.createInput(profile.profiles.item(0), path, FO.NewBodyFeatureOperation)
    return comp.features.sweepFeatures.add(inp)


def body_named(comp, ordinal):
    body = comp.bRepBodies.itemByName("Body" + str(ordinal))
    if body is None:
        raise RuntimeError("Control body missing: Body" + str(ordinal))
    return body


def add_body_step(comp, features, step):
    feats = comp.features
    if step["kind"] == "combine":
        tools = coll(*[body_named(comp, ordinal) for ordinal in step["tools"]])
        inp = feats.combineFeatures.createInput(body_named(comp, step["target"]), tools)
        inp.operation = OPERATIONS[step["operation"]]
        inp.isKeepToolBodies = step["keep"]
        return feats.combineFeatures.add(inp)
    if step["kind"] == "split":
        inp = feats.splitBodyFeatures.createInput(body_named(comp, step["target"]), features[step["plane"]], True)
        return feats.splitBodyFeatures.add(inp)
    if step["kind"] == "paste":
        return feats.copyPasteBodies.add(body_named(comp, step["source_body"]))
    source = coll(body_named(comp, step["source_body"]))
    if step["kind"] == "body_pattern":
        count = adsk.core.ValueInput.createByReal(step["count_u"])
        inp = feats.rectangularPatternFeatures.createInput(source, comp.xConstructionAxis, count, vi(step["spacing_u"]), adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
        inp.setDirectionTwo(comp.yConstructionAxis, adsk.core.ValueInput.createByReal(step["count_v"]), vi(step["spacing_v"]))
        return feats.rectangularPatternFeatures.add(inp)
    inp = feats.circularPatternFeatures.createInput(source, comp.zConstructionAxis)
    inp.quantity = adsk.core.ValueInput.createByReal(step["count"])
    inp.totalAngle = vi(step["angle"])
    inp.isSymmetric = False
    return feats.circularPatternFeatures.add(inp)


def level_edge(body, x, y, z):
    found = body.parentComponent.findBRepUsingPoint(pt(x, y, z), adsk.fusion.BRepEntityTypes.BRepEdgeEntityType, 1e-6, False)
    edges = [adsk.fusion.BRepEdge.cast(found.item(i)) for i in range(found.count)]
    edges = [edge for edge in edges if edge is not None and edge.body == body]
    if len(edges) != 1:
        raise RuntimeError("Level edge not unique at " + str((x, y, z)))
    return edges[0]


def corner_edges(body, step):
    corners = step.get("corners_cm", [step["corner_cm"]])
    if "level_cm" in step:
        return coll(*[level_edge(body, x, y, step["level_cm"]) for x, y in corners])
    return coll(*[vertical_edge(body, *corner) for corner in corners])


def build_control(comp, entry):
    body = None
    if entry.get("base", "cuboid") == "cuboid":
        sketch = comp.sketches.add(comp.xYConstructionPlane)
        sketch.name = "Base Sketch"
        sketch.sketchCurves.sketchLines.addTwoPointRectangle(pt(0, 0), pt(4, 3))
        extrude = comp.features.extrudeFeatures.addSimple(sketch.profiles.item(0), vi("20 mm"), FO.NewBodyFeatureOperation)
        extrude.name = "Base Extrude"
        body = extrude.bodies.item(0)
    features = []
    for step in entry["steps"]:
        if step["kind"] == "extrude":
            feature = add_extrude(comp, step)
        elif step["kind"] == "revolve":
            feature = add_revolve(comp, step)
        elif step["kind"] == "loft":
            feature = add_loft(comp, step)
        elif step["kind"] == "sweep":
            feature = add_sweep(comp, step)
        elif step["kind"] == "hole":
            feature = add_hole(comp, body, step)
        elif step["kind"] in ("pattern", "circular", "mirror"):
            feature = add_copy(comp, features, step)
        elif step["kind"] == "plane":
            feature = add_plane(comp, step)
        elif step["kind"] in ("combine", "split", "body_pattern", "body_ring", "paste"):
            feature = add_body_step(comp, features, step)
        elif step["kind"] == "axis":
            inp = comp.constructionAxes.createInput()
            inp.setByEdge(vertical_edge(body, *step["corner_cm"]))
            feature = comp.constructionAxes.add(inp)
        elif step["kind"] == "point":
            inp = comp.constructionPoints.createInput()
            inp.setByPoint(corner_vertex(body, *step["corner_cm"]))
            feature = comp.constructionPoints.add(inp)
        elif step["kind"] == "draft":
            feats = comp.features.draftFeatures
            sides, floor = draft_faces(body)
            inp = feats.createInput(sides, floor, True)
            inp.setSingleAngle(False, vi(step["angle"]))
            feature = feats.add(inp)
        elif step["kind"] == "offset":
            feats = comp.features.offsetFacesFeatures
            face = side_face(body, *step["side_cm"]) if "side_cm" in step else top_face(body)
            feature = feats.add(feats.createInput([face], vi(step["amount"])))
        elif step["kind"] == "move":
            feats = comp.features.moveFeatures
            matrix = adsk.core.Matrix3D.create()
            matrix.setToRotation(radians(step["turn_degrees"]), adsk.core.Vector3D.create(0, 0, 1), pt(0, 0, 0))
            matrix.translation = adsk.core.Vector3D.create(*step["offset_cm"])
            feature = feats.add(feats.createInput(coll(body), matrix))
        elif step["kind"] == "fillet":
            feats = comp.features.filletFeatures
            inp = feats.createInput()
            inp.edgeSetInputs.addConstantRadiusEdgeSet(corner_edges(body, step), vi(step["amount"]), True)
            feature = feats.add(inp)
        elif step["kind"] == "chamfer":
            feats = comp.features.chamferFeatures
            inp = feats.createInput2()
            edges = corner_edges(body, step)
            if "second" in step:
                inp.chamferEdgeSets.addTwoDistancesChamferEdgeSet(edges, vi(step["amount"]), vi(step["second"]), False, True)
            elif "angle" in step:
                inp.chamferEdgeSets.addDistanceAndAngleChamferEdgeSet(edges, vi(step["amount"]), vi(step["angle"]), False, True)
            else:
                inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, vi(step["amount"]), True)
            feature = feats.add(inp)
        else:
            feats = comp.features.shellFeatures
            faces = [top_face(body)] + [side_face(body, *point) for point in step.get("sides_cm", [])]
            inp = feats.createInput(coll(*faces), False)
            inp.insideThickness = vi(step["amount"])
            feature = feats.add(inp)
        feature.name = step["name"]
        features.append(feature)
        body = comp.bRepBodies.item(0) if comp.bRepBodies.count else None


def work_geometry(comp):
    work = []
    for item in list(comp.constructionAxes) + list(comp.constructionPoints):
        values = None
        try:
            geometry = item.geometry
            if geometry is not None and hasattr(geometry, "direction"):
                direction = geometry.direction.copy()
                direction.normalize()
                values = list(geometry.origin.asArray()) + list(direction.asArray())
            elif geometry is not None:
                values = list(geometry.asArray())
        except Exception:
            values = None
        work.append({"name": item.name, "values": values})
    return work


def observe(design):
    comp = design.rootComponent
    bodies = []
    for b in comp.bRepBodies:
        bb = b.boundingBox
        props = b.physicalProperties
        bodies.append({
            "name": b.name,
            "solid": b.isSolid,
            "volume_cm3": b.volume,
            "area_cm2": b.area,
            "faces": b.faces.count,
            "edges": b.edges.count,
            "vertices": b.vertices.count,
            "min_cm": list(bb.minPoint.asArray()),
            "max_cm": list(bb.maxPoint.asArray()),
            "center_cm": list(props.centerOfMass.asArray()),
            "surface_types": sorted(f.geometry.surfaceType for f in b.faces),
        })
    timeline = [{"name": i.name, "health": i.healthState, "message": i.errorOrWarningMessage, "rolled_back": i.isRolledBack} for i in design.timeline]
    params = []
    for p in design.allParameters:
        owner = None
        try:
            owner = p.createdBy.name if p.createdBy else None
        except Exception:
            owner = None
        role = None
        try:
            role = adsk.fusion.ModelParameter.cast(p).role if adsk.fusion.ModelParameter.cast(p) else None
        except Exception:
            role = None
        params.append({"name": p.name, "expression": p.expression, "value": p.value, "unit": p.unit, "owner": owner, "role": role})
    return {"timeline": timeline, "bodies": bodies, "parameters": params, "work": work_geometry(comp), "marker": design.timeline.markerPosition}


def healthy(observed):
    return all(i["health"] == HEALTHY and not i["message"] for i in observed["timeline"] if not i["rolled_back"])


def same_work(left, right):
    if [w["name"] for w in left] != [w["name"] for w in right]:
        return False
    for a, b in zip(left, right):
        if (a["values"] is None) != (b["values"] is None):
            return False
        if a["values"] is not None and (len(a["values"]) != len(b["values"]) or not all(isclose(x, y, rel_tol=1e-7, abs_tol=1e-7) for x, y in zip(a["values"], b["values"]))):
            return False
    return True


def same_geometry(left, right):
    if len(left["bodies"]) != len(right["bodies"]):
        return False
    if not same_work(left.get("work", []), right.get("work", [])):
        return False
    for a, b in zip(left["bodies"], right["bodies"]):
        if (a["faces"], a["edges"], a["vertices"], a["solid"], a["surface_types"]) != (b["faces"], b["edges"], b["vertices"], b["solid"], b["surface_types"]):
            return False
        if not isclose(a["volume_cm3"], b["volume_cm3"], rel_tol=1e-8, abs_tol=1e-9) or not isclose(a["area_cm2"], b["area_cm2"], rel_tol=1e-8, abs_tol=1e-9):
            return False
        bounds = zip(a["min_cm"] + a["max_cm"] + a["center_cm"], b["min_cm"] + b["max_cm"] + b["center_cm"])
        if not all(isclose(x, y, rel_tol=1e-7, abs_tol=1e-7) for x, y in bounds):
            return False
    return True


def walk_markers(design):
    result = []
    for position in range(design.timeline.count + 1):
        design.timeline.markerPosition = position
        result.append(observe(design))
    if not design.timeline.moveToEnd():
        raise RuntimeError("Timeline did not return to the end")
    return result


def apply_edits(design, edits):
    comp = design.rootComponent
    for edit in edits:
        if edit["feature"] == "height":
            extent = adsk.fusion.DistanceExtentDefinition.cast(comp.features.extrudeFeatures.item(0).extentOne)
            extent.distance.expression = edit["expression"]
            continue
        owned = [p for p in comp.modelParameters if p.createdBy is not None and p.createdBy.name == edit["feature"]]
        matches = [p for p in owned if (p.role == edit["role"] if "role" in edit else p.unit == "mm")]
        if len(matches) != 1:
            raise RuntimeError("Driving parameter not unique for " + edit["feature"] + ": " + str([(p.name, p.role) for p in owned]))
        matches[0].expression = edit["expression"]
    if not design.computeAll():
        raise RuntimeError("computeAll failed after parameter edits")


def open_archive(path):
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    if doc is None:
        raise RuntimeError("Document did not open: " + path.name)
    open_docs.append(doc)
    return doc, adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))


def close(doc):
    if doc in open_docs:
        open_docs.remove(doc)
    doc.close(False)


def native_control(entry):
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    open_docs.append(doc)
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    build_control(design.rootComponent, entry)
    built = observe(design)
    markers = walk_markers(design)
    apply_edits(design, entry["edits"])
    edited = observe(design)
    close(doc)
    return {"built": built, "markers": markers, "edited": edited}


def compare(case, label, observed, expected):
    result = {"healthy": healthy(observed), "matches_control": same_geometry(observed, expected)}
    case["checks"][label] = result
    return result["healthy"] and result["matches_control"]


try:
    for name, entry in manifest.items():
        source = root / entry["file"]
        case = {"name": name, "file": entry["file"], "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "steps": entry["steps"], "edits": entry["edits"], "kit_states": entry["kit_states"], "checks": {}, "stage": "control"}
        report["cases"].append(case)
        checkpoint()
        doc = None
        before = list(app.documents)
        try:
            if case["sha256"] != entry["sha256"]:
                raise RuntimeError("Authored digest differs from the manifest")
            control = native_control(entry)
            case["control"] = control
            case["stage"] = "opening"
            checkpoint()
            doc, design = open_archive(source)
            case["opened"] = observe(design)
            ok = compare(case, "opened", case["opened"], control["built"])
            case["stage"] = "markers"
            checkpoint()
            markers = walk_markers(design)
            case["markers"] = markers
            marker_ok = []
            for position, (kit, native) in enumerate(zip(markers, control["markers"])):
                marker_ok.append(healthy(kit) and same_geometry(kit, native))
            case["checks"]["markers"] = {"positions": len(markers), "control_positions": len(control["markers"]), "each": marker_ok}
            ok = ok and len(markers) == len(control["markers"]) and all(marker_ok)
            case["computed"] = design.computeAll()
            case["recomputed"] = observe(design)
            ok = compare(case, "recomputed", case["recomputed"], control["built"]) and case["computed"] and ok
            case["stage"] = "editing"
            checkpoint()
            apply_edits(design, entry["edits"])
            case["edited"] = observe(design)
            ok = compare(case, "edited", case["edited"], control["edited"]) and ok
            saved = root / ("vendor_" + name + ".f3d")
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
                raise RuntimeError("Export failed")
            close(doc)
            doc = None
            case["stage"] = "reopening"
            checkpoint()
            doc, design = open_archive(saved)
            case["reopened"] = observe(design)
            ok = compare(case, "reopened", case["reopened"], control["edited"]) and ok
            expressions = sorted((p["owner"] or "", p["expression"]) for p in case["reopened"]["parameters"])
            edited_expressions = sorted((p["owner"] or "", p["expression"]) for p in case["edited"]["parameters"])
            case["checks"]["reopened_parameters_preserved"] = expressions == edited_expressions
            ok = ok and expressions == edited_expressions
            case["reopen_computed"] = design.computeAll()
            case["reopen_recomputed"] = observe(design)
            ok = compare(case, "reopen_recomputed", case["reopen_recomputed"], control["edited"]) and case["reopen_computed"] and ok
            case["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
            close(doc)
            doc = None
            case["status"] = "accepted" if ok else "rejected"
        except Exception:
            case["status"] = "failed"
            case["traceback"] = traceback.format_exc()
        finally:
            for item in list(open_docs):
                close(item)
            for item in list(app.documents):
                if item not in before and item.isValid:
                    case.setdefault("stray_closed", []).append(item.name)
                    item.close(False)
            case["stage"] = "done"
            checkpoint()
    report["status"] = "accepted" if all(c.get("status") == "accepted" for c in report["cases"]) else "rejected"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
finally:
    for item in list(open_docs):
        try:
            close(item)
        except Exception:
            pass
    if original is not None and original.isValid:
        original.activate()
    report["documents_after"] = app.documents.count
    checkpoint()
