import hashlib
import json
import math
import re
import traceback
import uuid
from pathlib import Path

import adsk.core
import adsk.fusion

CONTROL = "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
CONTROL_VOLUME_MM3 = 30000.0
ACCURACY = adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy
BASES = {
    "XY": {"plane": "xYConstructionPlane", "u": (1, 0, 0), "v": (0, 1, 0), "n": (0, 0, 1)},
    "YZ": {"plane": "yZConstructionPlane", "u": (0, 1, 0), "v": (0, 0, 1), "n": (1, 0, 0)},
    "XZ": {"plane": "xZConstructionPlane", "u": (1, 0, 0), "v": (0, 0, 1), "n": (0, -1, 0)},
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def design_of(document):
    return adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))


def mm(value_cm):
    return round(value_cm * 10.0, 9)


def point_mm(point):
    return [mm(point.x), mm(point.y), mm(point.z)]


def world(basis, u, v, n=0.0):
    axes = BASES[basis]
    return tuple(u * axes["u"][index] + v * axes["v"][index] + n * axes["n"][index] for index in range(3))


def health(entity):
    state = getattr(entity, "healthState", None)
    names = {0: "healthy", 1: "warning", 2: "error", 3: "unknown"}
    return {"state": names.get(state, str(state)), "message": getattr(entity, "errorOrWarningMessage", "") or ""}


def names(collection):
    if collection is None:
        return []
    return [collection.item(index).name for index in range(collection.count)]


def body_evidence(design):
    root = design.rootComponent
    bodies = [root.bRepBodies.item(index) for index in range(root.bRepBodies.count)]
    if not bodies:
        return {"body_count": 0, "volume_mm3": None, "center_of_mass_mm": None, "mass_properties": "not_applicable_no_body", "bodies": []}
    properties = root.getPhysicalProperties(ACCURACY)
    rows = []
    for body in bodies:
        box = body.boundingBox
        rows.append({
            "name": body.name, "solid": body.isSolid, "volume_mm3": round(body.volume * 1000.0, 9),
            "faces": body.faces.count, "edges": body.edges.count, "vertices": body.vertices.count,
            "bounding_box_mm": [point_mm(box.minPoint), point_mm(box.maxPoint)],
        })
    return {
        "body_count": len(bodies), "volume_mm3": round(sum(row["volume_mm3"] for row in rows), 9),
        "center_of_mass_mm": point_mm(properties.centerOfMass), "mass_properties": "measured", "bodies": rows,
    }


def curve_evidence(sketch):
    rows = []
    curves = sketch.sketchCurves
    for index in range(curves.count):
        curve = curves.item(index)
        row = {"type": curve.objectType.split("::")[-1], "index": index, "construction": curve.isConstruction,
               "fixed": curve.isFixed, "reference": curve.isReference}
        if hasattr(curve, "startSketchPoint") and curve.startSketchPoint is not None:
            row["start_world_mm"] = point_mm(curve.startSketchPoint.worldGeometry)
            row["end_world_mm"] = point_mm(curve.endSketchPoint.worldGeometry)
        if hasattr(curve, "centerSketchPoint") and curve.centerSketchPoint is not None:
            row["center_world_mm"] = point_mm(curve.centerSketchPoint.worldGeometry)
        if hasattr(curve, "radius"):
            row["radius_mm"] = mm(curve.radius)
        rows.append(row)
    return rows


def sketch_evidence(sketch):
    constraints = [{"type": item.objectType.split("::")[-1]} for item in (sketch.geometricConstraints.item(index) for index in range(sketch.geometricConstraints.count))]
    dimensions = []
    for index in range(sketch.sketchDimensions.count):
        dimension = sketch.sketchDimensions.item(index)
        parameter = dimension.parameter
        dimensions.append({
            "type": dimension.objectType.split("::")[-1], "driving": dimension.isDriving,
            "parameter": parameter.name if parameter else None, "expression": parameter.expression if parameter else None,
        })
    areas = []
    for index in range(sketch.profiles.count):
        areas.append(round(sketch.profiles.item(index).areaProperties(ACCURACY).area * 100.0, 9))
    try:
        plane = sketch.referencePlane
        support, support_name = plane.objectType.split("::")[-1], getattr(plane, "name", None)
    except RuntimeError as error:
        support, support_name = "BRepFace", "not read without a timeline rollback: " + str(error)
    return {
        "name": sketch.name, "support": support, "support_name": support_name,
        "origin_world_mm": point_mm(sketch.origin), "x_direction": sketch.xDirection.asArray(), "y_direction": sketch.yDirection.asArray(),
        "curves": curve_evidence(sketch), "point_count": sketch.sketchPoints.count,
        "constraints": constraints, "dimensions": dimensions, "profile_areas_mm2": sorted(areas),
        "fully_constrained": getattr(sketch, "isFullyConstrained", None), "health": health(sketch),
    }


def parameter_evidence(design):
    rows = []
    for index in range(design.allParameters.count):
        parameter = design.allParameters.item(index)
        rows.append({
            "name": parameter.name, "kind": parameter.objectType.split("::")[-1], "expression": parameter.expression,
            "unit": parameter.unit, "value_internal": parameter.value, "role": getattr(parameter, "role", None),
            "dependencies": names(getattr(parameter, "dependencyParameters", None)),
            "dependents": names(getattr(parameter, "dependentParameters", None)),
        })
    return rows


def timeline_evidence(design):
    rows = []
    for index in range(design.timeline.count):
        item = design.timeline.item(index)
        entity = item.entity
        rows.append({"index": index, "name": item.name, "type": entity.objectType.split("::")[-1] if entity else None,
                     "suppressed": item.isSuppressed, "rolled_back": item.isRolledBack, "health": health(item)})
    return rows


def measure(document, label):
    design = design_of(document)
    sketches = design.rootComponent.sketches
    return {
        "label": label, "document_units": design.fusionUnitsManager.distanceDisplayUnits,
        "design_type": "parametric" if design.designType == adsk.fusion.DesignTypes.ParametricDesignType else "direct",
        "feature_tree": timeline_evidence(design), "parameters": parameter_evidence(design),
        "sketches": [sketch_evidence(sketches.item(index)) for index in range(sketches.count)],
        **body_evidence(design),
    }


def export(document, path, saves):
    design = design_of(document)
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):
        raise RuntimeError("Fusion archive export failed: " + path.name)
    saves.append({"file": path.name, "sha256": digest(path), "size_bytes": path.stat().st_size})


def reopen(app, path, owned):
    document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    if document is None:
        raise RuntimeError("Archive import did not return an owned new document: " + Path(path).name)
    owned.append(document)
    return document


def close(document, owned):
    document.close(False)
    owned.remove(document)


def control_check(app, repo, owned, label):
    document = reopen(app, repo / CONTROL, owned)
    try:
        design_of(document).computeAll()
        evidence = body_evidence(design_of(document))
        evidence.update({"label": label, "file": CONTROL, "sha256": digest(repo / CONTROL), "expected_volume_mm3": CONTROL_VOLUME_MM3})
        evidence["healthy"] = evidence["body_count"] == 1 and abs(evidence["volume_mm3"] - CONTROL_VOLUME_MM3) <= max(1e-6, 1e-9 * CONTROL_VOLUME_MM3)
        return evidence
    finally:
        close(document, owned)


def new_design(app):
    document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = design_of(document)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    return document, design, design.rootComponent


def sketch_point(sketch, world_mm):
    return sketch.modelToSketchSpace(adsk.core.Point3D.create(*(value / 10.0 for value in world_mm)))


def is_horizontal(line):
    start, end = line.startSketchPoint.geometry, line.endSketchPoint.geometry
    return abs(end.y - start.y) < 1e-9


def line_orientation(line):
    orientations = adsk.fusion.DimensionOrientations
    return orientations.HorizontalDimensionOrientation if is_horizontal(line) else orientations.VerticalDimensionOrientation


def axis_orientation(sketch, origin_world_mm, direction_world):
    start = sketch_point(sketch, origin_world_mm)
    end = sketch_point(sketch, tuple(origin_world_mm[index] + direction_world[index] for index in range(3)))
    orientations = adsk.fusion.DimensionOrientations
    return orientations.HorizontalDimensionOrientation if abs(end.x - start.x) > abs(end.y - start.y) else orientations.VerticalDimensionOrientation


def offset_point(sketch, first, second, offset_cm):
    a, b = first.geometry, second.geometry
    middle = adsk.core.Point3D.create((a.x + b.x) / 2.0, (a.y + b.y) / 2.0, 0)
    if abs(b.y - a.y) < abs(b.x - a.x):
        middle.y -= offset_cm
    else:
        middle.x -= offset_cm
    return middle


def name_parameter(dimension, name, expression):
    dimension.parameter.name = name
    dimension.parameter.expression = expression
    return dimension.parameter


def rectangle(sketch, corners_world_mm):
    corners = [sketch_point(sketch, corner) for corner in corners_world_mm]
    lines = sketch.sketchCurves.sketchLines
    bottom = lines.addByTwoPoints(corners[0], corners[1])
    right = lines.addByTwoPoints(bottom.endSketchPoint, corners[2])
    top = lines.addByTwoPoints(right.endSketchPoint, corners[3])
    left = lines.addByTwoPoints(top.endSketchPoint, bottom.startSketchPoint)
    for line in (bottom, right, top, left):
        if is_horizontal(line):
            sketch.geometricConstraints.addHorizontal(line)
        else:
            sketch.geometricConstraints.addVertical(line)
    return bottom, right, top, left


def driving_rectangle(sketch, basis, width_name, height_name, width, height, offset_n=0.0):
    corners = [world(basis, 0, 0, offset_n), world(basis, width, 0, offset_n), world(basis, width, height, offset_n), world(basis, 0, height, offset_n)]
    bottom, right, top, left = rectangle(sketch, corners)
    sketch.geometricConstraints.addCoincident(bottom.startSketchPoint, sketch.originPoint)
    dimensions = sketch.sketchDimensions
    name_parameter(dimensions.addDistanceDimension(bottom.startSketchPoint, bottom.endSketchPoint, line_orientation(bottom), offset_point(sketch, bottom.startSketchPoint, bottom.endSketchPoint, 0.8)), width_name, "{} mm".format(width))
    name_parameter(dimensions.addDistanceDimension(left.startSketchPoint, left.endSketchPoint, line_orientation(left), offset_point(sketch, left.startSketchPoint, left.endSketchPoint, 0.8)), height_name, "{} mm".format(height))
    return bottom, right, top, left


def extrude(root, profile, name, expression, operation, direction, termination="blind"):
    features = root.features.extrudeFeatures
    entry = features.createInput(profile, operation)
    extent_direction = adsk.fusion.ExtentDirections.PositiveExtentDirection if direction > 0 else adsk.fusion.ExtentDirections.NegativeExtentDirection
    if termination == "through_all":
        entry.setOneSideExtent(adsk.fusion.ThroughAllExtentDefinition.create(), extent_direction)
    else:
        entry.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(expression)), extent_direction)
    feature = features.add(entry)
    if termination != "through_all":
        adsk.fusion.DistanceExtentDefinition.cast(feature.extentOne).distance.name = name
    return feature


def build_rectangle_sketch(app, options):
    document, design, root = new_design(app)
    basis = options["basis"]
    sketch = root.sketches.add(getattr(root, BASES[basis]["plane"]))
    sketch.name = "RectangleSketch"
    driving_rectangle(sketch, basis, "width_mm", "height_mm", 40, 20)
    design.computeAll()
    return document


def build_circle_sketch(app, options):
    document, design, root = new_design(app)
    sketch = root.sketches.add(getattr(root, BASES[options["basis"]]["plane"]))
    sketch.name = "CircleSketch"
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(sketch_point(sketch, (0, 0, 0)), 0.5)
    sketch.geometricConstraints.addCoincident(circle.centerSketchPoint, sketch.originPoint)
    name_parameter(sketch.sketchDimensions.addDiameterDimension(circle, adsk.core.Point3D.create(0.8, 0.8, 0)), "diameter_mm", "10 mm")
    design.computeAll()
    return document


def build_boss(app, options):
    document, design, root = new_design(app)
    basis = options["basis"]
    sketch = root.sketches.add(getattr(root, BASES[basis]["plane"]))
    sketch.name = "RectangleSketch"
    driving_rectangle(sketch, basis, "width_mm", "height_mm", 40, 20)
    boss = extrude(root, sketch.profiles.item(0), "depth_mm", "10 mm", adsk.fusion.FeatureOperations.NewBodyFeatureOperation, options.get("direction", 1))
    boss.name = "BlindBoss"
    design.computeAll()
    return document, design, root, boss


def build_boss_document(app, options):
    return build_boss(app, options)[0]


def top_face(body, basis, depth):
    normal = BASES[basis]["n"]
    for index in range(body.faces.count):
        face = body.faces.item(index)
        if adsk.core.Plane.cast(face.geometry) is None:
            continue
        point = face.pointOnFace
        found, face_normal = face.evaluator.getNormalAtPoint(point)
        height = sum(point.asArray()[axis] * 10.0 * normal[axis] for axis in range(3))
        if found and all(abs(face_normal.asArray()[axis] - normal[axis]) < 1e-9 for axis in range(3)) and abs(height - depth) < 1e-6:
            return face
    raise RuntimeError("Top planar face of the parent boss was not found")


def build_cut(app, options):
    document, design, root, boss = build_boss(app, options)
    basis = options["basis"]
    face = top_face(boss.bodies.item(0), basis, 10.0)
    sketch = root.sketches.add(face)
    sketch.name = "CutSketch"
    corners = [world(basis, 15, 6, 10), world(basis, 25, 6, 10), world(basis, 25, 14, 10), world(basis, 15, 14, 10)]
    bottom, right, top, left = rectangle(sketch, corners)
    diagonal = sketch.sketchCurves.sketchLines.addByTwoPoints(bottom.startSketchPoint, top.startSketchPoint)
    diagonal.isConstruction = True
    center = sketch.sketchPoints.add(sketch_point(sketch, world(basis, 20, 10, 10)))
    sketch.geometricConstraints.addMidPoint(center, diagonal)
    projected = sketch.project(root.originConstructionPoint).item(0)
    dimensions = sketch.sketchDimensions
    name_parameter(dimensions.addDistanceDimension(bottom.startSketchPoint, bottom.endSketchPoint, line_orientation(bottom), offset_point(sketch, bottom.startSketchPoint, bottom.endSketchPoint, 0.4)), "cut_width_mm", "10 mm")
    name_parameter(dimensions.addDistanceDimension(left.startSketchPoint, left.endSketchPoint, line_orientation(left), offset_point(sketch, left.startSketchPoint, left.endSketchPoint, 0.4)), "cut_height_mm", "8 mm")
    origin_world = world(basis, 0, 0, 10)
    u_dimension = dimensions.addDistanceDimension(projected, center, axis_orientation(sketch, origin_world, BASES[basis]["u"]), offset_point(sketch, projected, center, 1.2))
    v_dimension = dimensions.addDistanceDimension(projected, center, axis_orientation(sketch, origin_world, BASES[basis]["v"]), offset_point(sketch, projected, center, -1.2))
    name_parameter(u_dimension, "cut_center_u_mm", "width_mm / 2")
    name_parameter(v_dimension, "cut_center_v_mm", "height_mm / 2")
    areas = [(sketch.profiles.item(index).areaProperties(ACCURACY).area, index) for index in range(sketch.profiles.count)]
    profile = sketch.profiles.item(min(areas)[1])
    termination = options.get("termination", "blind")
    cut = extrude(root, profile, "cut_depth_mm", "4 mm", adsk.fusion.FeatureOperations.CutFeatureOperation, -1, termination)
    cut.name = "BlindCut" if termination == "blind" else "ThroughAllCut"
    design.computeAll()
    return document


def build_revolution(app, options):
    document, design, root = new_design(app)
    sketch = root.sketches.add(root.xZConstructionPlane)
    sketch.name = "AnnulusProfile"
    corners = [world("XZ", 2, 0), world("XZ", 6, 0), world("XZ", 6, 12), world("XZ", 2, 12)]
    bottom, right, top, left = rectangle(sketch, corners)
    axis_line = sketch.project(root.xConstructionAxis).item(0)
    sketch.geometricConstraints.addCoincident(bottom.startSketchPoint, axis_line)
    dimensions = sketch.sketchDimensions
    radial = axis_orientation(sketch, (0, 0, 0), (1, 0, 0))
    name_parameter(dimensions.addDistanceDimension(sketch.originPoint, bottom.startSketchPoint, radial, offset_point(sketch, sketch.originPoint, bottom.startSketchPoint, 0.6)), "inner_radius_mm", "2 mm")
    name_parameter(dimensions.addDistanceDimension(sketch.originPoint, bottom.endSketchPoint, radial, offset_point(sketch, sketch.originPoint, bottom.endSketchPoint, 1.2)), "outer_radius_mm", "6 mm")
    name_parameter(dimensions.addDistanceDimension(left.startSketchPoint, left.endSketchPoint, line_orientation(left), offset_point(sketch, left.startSketchPoint, left.endSketchPoint, 0.6)), "height_mm", "12 mm")
    features = root.features.revolveFeatures
    entry = features.createInput(sketch.profiles.item(0), root.zConstructionAxis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    entry.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
    feature = features.add(entry)
    feature.name = "Revolution"
    angle = adsk.fusion.AngleExtentDefinition.cast(feature.extentDefinition)
    angle.angle.name = "angle_deg"
    design.computeAll()
    return document


def expected(recipe_id, values):
    if recipe_id == "P01":
        return {"area_mm2": values["width_mm"] * values["height_mm"]}
    if recipe_id == "P02":
        return {"area_mm2": math.pi * values["diameter_mm"] ** 2 / 4.0}
    if recipe_id == "P03":
        w, h, d = values["width_mm"], values["height_mm"], values["depth_mm"]
        sign = values.get("direction", 1)
        return {"volume_mm3": w * h * d, "center_of_mass_mm": [w / 2.0, h / 2.0, sign * d / 2.0]}
    if recipe_id == "P04":
        w, h, d = values["width_mm"], values["height_mm"], values["depth_mm"]
        cw, ch, cd = values["cut_width_mm"], values["cut_height_mm"], values["cut_depth_mm"]
        volume = w * h * d - cw * ch * cd
        return {"volume_mm3": volume, "center_of_mass_mm": [w / 2.0, h / 2.0, (w * h * d * d / 2.0 - cw * ch * cd * (d - cd / 2.0)) / volume]}
    if recipe_id == "P05":
        ri, ro, h = values["inner_radius_mm"], values["outer_radius_mm"], values["height_mm"]
        angle = math.radians(values["angle_deg"])
        k = 2.0 * (ro ** 3 - ri ** 3) / (3.0 * angle * (ro ** 2 - ri ** 2))
        return {"volume_mm3": angle * (ro ** 2 - ri ** 2) * h / 2.0, "center_of_mass_mm": [k * math.sin(angle), k * (1.0 - math.cos(angle)), h / 2.0]}
    return {}


def map_world(basis, vector):
    return list(world(basis, vector[0], vector[1], vector[2]))


def compare(recipe_id, basis, values, reading):
    analytic = expected(recipe_id, values)
    result = {"classification": "analytic_expectation_for_comparison_only", "expected": analytic, "matches": True}
    if "area_mm2" in analytic:
        areas = reading["sketches"][0]["profile_areas_mm2"] if reading["sketches"] else []
        result["matches"] = bool(areas) and abs(max(areas) - analytic["area_mm2"]) <= 1e-6 * max(1.0, analytic["area_mm2"])
    if "volume_mm3" in analytic:
        center = list(analytic["center_of_mass_mm"]) if recipe_id == "P05" else map_world(basis, analytic["center_of_mass_mm"])
        result["expected_center_world_mm"] = center
        result["matches"] = (reading["body_count"] == 1 and abs(reading["volume_mm3"] - analytic["volume_mm3"]) <= max(1e-6, 1e-9 * analytic["volume_mm3"])
                             and all(abs(reading["center_of_mass_mm"][axis] - center[axis]) <= 1e-6 for axis in range(3)))
    return result


def edited_expression(original, value, unit):
    numbers = re.findall(r"[0-9]+(?:\.[0-9]+)?", original)
    if len(numbers) != 1:
        return "{} {}".format(value, unit)
    return re.sub(r"[0-9]+(?:\.[0-9]+)?", str(value), original, count=1)


def edit_unit(parameter):
    return "deg" if parameter == "angle_deg" else "mm"


def edit_cycle(app, document, recipe, basis, output, saves, owned):
    design = design_of(document)
    rows = []
    for edit in recipe["independent_edits"]:
        name = edit["parameter"]
        parameter = design.allParameters.itemByName(name)
        if parameter is None:
            raise RuntimeError("Driving parameter is missing: " + name)
        original = parameter.expression
        parameter.expression = edited_expression(original, edit["value"], edit_unit(name))
        design.computeAll()
        edited = measure(document, "edit " + name + " = " + str(edit["value"]))
        values = dict(recipe["driving_parameters"], **{name: edit["value"]})
        file = output / "{}-fusion-edit-{}-{}.f3d".format(recipe["id"], name, edit["value"])
        export(document, file, saves)
        parameter.expression = original
        design.computeAll()
        restored = measure(document, "restore " + name)
        check = reopen(app, file, owned)
        try:
            design_of(check).computeAll()
            reopened = measure(check, "fresh reopen of " + file.name)
        finally:
            close(check, owned)
        rows.append({"edit": edit, "edited": edited, "edited_comparison": compare(recipe["id"], basis, values, edited),
                     "export": file.name, "reopened": reopened, "reopened_comparison": compare(recipe["id"], basis, values, reopened),
                     "restored": restored, "restored_comparison": compare(recipe["id"], basis, recipe["driving_parameters"], restored)})
    return rows


def variant(app, recipe, label, file, saves, owned, document, basis, values):
    before = measure(document, label)
    export(document, file, saves)
    check = reopen(app, file, owned)
    try:
        design_of(check).computeAll()
        reopened = measure(check, "fresh reopen of " + file.name)
    finally:
        close(check, owned)
    return {"label": label, "export": file.name, "before_save": before, "reopened": reopened,
            "comparison": compare(recipe["id"], basis, values, reopened)}


BUILDERS = {"P01": build_rectangle_sketch, "P02": build_circle_sketch, "P03": build_boss_document, "P04": build_cut, "P05": build_revolution}
BASE_PLANE = {"P01": "XY", "P02": "XY", "P03": "XY", "P04": "XY", "P05": "XZ"}


def variants(recipe_id):
    rows = [("units-inch", "display units inches", {}, None)]
    if recipe_id != "P05":
        rows.append(("plane-yz", "baseline reauthored on YZ", {"basis": "YZ"}, "YZ"))
    if recipe_id == "P03":
        rows.append(("direction-negative", "boss reversed to -n with unchanged depth", {"direction": -1}, None))
    if recipe_id == "P04":
        rows.append(("termination-through-all", "cut reauthored as through-all", {"termination": "through_all"}, None))
    return rows


def capture(recipe_id, script_path):
    app = adsk.core.Application.get()
    folder = Path(script_path).resolve().parent
    repo = folder.parents[3]
    specs = json.loads((repo / "re/automation/PairSpecs.json").read_text(encoding="utf-8"))
    recipe = next(item for item in specs["recipes"] if item["id"] == recipe_id)
    output = folder / ("fusion-" + uuid.uuid4().hex[:12])
    output.mkdir()
    owned, saves, observations = [], [], {}
    base = BASE_PLANE[recipe_id]
    builder = BUILDERS[recipe_id]
    result = {
        "recipe_id": recipe_id, "application": "Autodesk Fusion", "exact_application_build": app.version,
        "authoring_recipe_sha256": hashlib.sha256(canonical(recipe)).hexdigest(),
        "specifications_sha256": digest(repo / "re/automation/PairSpecs.json"),
        "generator_sha256": digest(script_path), "shared_capture_sha256": digest(__file__),
        "authoring_origin": "Fusion API script authored from the {} recipe; no Kit reader, writer or source archive used".format(recipe_id),
        "world_basis": "Fusion world XYZ; baseline support {} with basis {}".format(base, BASES[base]),
        "configuration": "none", "saves": saves, "observations": observations, "errors": [],
        "limits": ["Repeat saves are separated by a document close and archive reopen in one Fusion process, not an application restart",
                   "Analytic comparisons are labelled separately and never replace measured observations"],
    }
    try:
        observations["healthy_control_before"] = control_check(app, repo, owned, "before")
        document = builder(app, {"basis": base})
        owned.append(document)
        observations["baseline"] = measure(document, "baseline after build")
        observations["baseline_comparison"] = compare(recipe_id, base, recipe["driving_parameters"], observations["baseline"])
        first = output / "{}-fusion-baseline-a.f3d".format(recipe_id)
        export(document, first, saves)
        close(document, owned)
        document = reopen(app, first, owned)
        observations["fresh_reopen"] = measure(document, "fresh reopen of baseline-a")
        design_of(document).computeAll()
        observations["unchanged_rebuild"] = measure(document, "unchanged rebuild after reopen")
        export(document, output / "{}-fusion-baseline-b.f3d".format(recipe_id), saves)
        observations["edits"] = edit_cycle(app, document, recipe, base, output, saves, owned)
        observations["variants"] = []
        for suffix, label, options, basis in variants(recipe_id):
            file = output / "{}-fusion-{}.f3d".format(recipe_id, suffix)
            values = dict(recipe["driving_parameters"], **({"direction": options["direction"]} if "direction" in options else {}))
            if suffix == "units-inch":
                design_of(document).fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.InchDistanceUnits
                design_of(document).computeAll()
                observations["variants"].append(variant(app, recipe, label, file, saves, owned, document, base, values))
                continue
            built = builder(app, dict({"basis": base}, **options))
            owned.append(built)
            try:
                reading = variant(app, recipe, label, file, saves, owned, built, basis or base, values)
                if suffix == "termination-through-all":
                    reading["comparison"] = {"classification": "no_analytic_expectation", "note": "through-all removes the full cut prism; compare measured readings only"}
                observations["variants"].append(reading)
            finally:
                close(built, owned)
        close(document, owned)
        observations["healthy_control_after"] = control_check(app, repo, owned, "after")
    except Exception:
        result["errors"].append(traceback.format_exc())
    finally:
        for document in list(owned):
            try:
                close(document, owned)
            except Exception:
                result["errors"].append("owned close failed: " + traceback.format_exc())
        measurements = output / "measurements.json"
        measurements.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        receipt = {"recipe_id": recipe_id, "measurements": measurements.name, "measurement_receipt_sha256": digest(measurements),
                   "native_files": saves, "errors": len(result["errors"])}
        (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (output / "complete.txt").write_text("{} Fusion capture finished; consult measurements.json errors.\n".format(recipe_id), encoding="utf-8")
