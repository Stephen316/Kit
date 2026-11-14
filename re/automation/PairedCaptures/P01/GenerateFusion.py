import hashlib
import json
import traceback
import uuid
from pathlib import Path

import adsk.core
import adsk.fusion

RECIPE_ID = "P01"
CONTROL = "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
CONTROL_VOLUME_MM3 = 30000.0


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


def health(entity):
    state = getattr(entity, "healthState", None)
    message = getattr(entity, "errorOrWarningMessage", "") or ""
    names = {0: "healthy", 1: "warning", 2: "error", 3: "unknown"}
    return {"state": names.get(state, str(state)), "message": message}


def body_evidence(design):
    root = design.rootComponent
    bodies = [root.bRepBodies.item(index) for index in range(root.bRepBodies.count)]
    if not bodies:
        return {"body_count": 0, "volume_mm3": None, "center_of_mass_mm": None, "mass_properties": "not_applicable_no_body"}
    properties = root.getPhysicalProperties(adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)
    return {
        "body_count": len(bodies),
        "volume_mm3": round(sum(body.volume for body in bodies) * 1000.0, 9),
        "center_of_mass_mm": point_mm(properties.centerOfMass),
        "mass_properties": "measured",
    }


def sketch_evidence(sketch):
    lines = sketch.sketchCurves.sketchLines
    entities = []
    for index in range(lines.count):
        line = lines.item(index)
        entities.append({
            "type": "SketchLine", "index": index,
            "start_mm": point_mm(line.startSketchPoint.geometry), "end_mm": point_mm(line.endSketchPoint.geometry),
            "construction": line.isConstruction, "fixed": line.isFixed,
        })
    other_curves = sketch.sketchCurves.count - lines.count
    constraints = []
    for index in range(sketch.geometricConstraints.count):
        constraint = sketch.geometricConstraints.item(index)
        constraints.append({"type": constraint.objectType.split("::")[-1], "deletable": constraint.isDeletable})
    dimensions = []
    for index in range(sketch.sketchDimensions.count):
        dimension = sketch.sketchDimensions.item(index)
        parameter = dimension.parameter
        dimensions.append({
            "type": dimension.objectType.split("::")[-1], "driving": dimension.isDriving,
            "parameter": parameter.name if parameter else None,
            "expression": parameter.expression if parameter else None,
            "value_mm": mm(parameter.value) if parameter else None,
        })
    areas = []
    for index in range(sketch.profiles.count):
        properties = sketch.profiles.item(index).areaProperties(adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)
        areas.append(round(properties.area * 100.0, 9))
    return {
        "name": sketch.name, "plane": sketch.referencePlane.name if hasattr(sketch.referencePlane, "name") else None,
        "origin_mm": point_mm(sketch.origin), "x_direction": sketch.xDirection.asArray(), "y_direction": sketch.yDirection.asArray(),
        "normal": sketch.referencePlane.geometry.normal.asArray() if hasattr(sketch.referencePlane, "geometry") else None,
        "entities": entities, "other_curve_count": other_curves,
        "point_count": sketch.sketchPoints.count, "constraints": constraints, "dimensions": dimensions,
        "profile_count": sketch.profiles.count, "profile_areas_mm2": areas,
        "fully_constrained": getattr(sketch, "isFullyConstrained", None),
        "health": health(sketch),
    }


def names(collection):
    if collection is None:
        return []
    return [collection.item(index).name for index in range(collection.count)]


def parameter_evidence(design):
    rows = []
    for index in range(design.allParameters.count):
        parameter = design.allParameters.item(index)
        rows.append({
            "name": parameter.name, "kind": parameter.objectType.split("::")[-1],
            "expression": parameter.expression, "unit": parameter.unit,
            "value_internal_cm": parameter.value, "value_mm": mm(parameter.value) if parameter.unit == "mm" else None,
            "role": getattr(parameter, "role", None),
            "dependencies": names(getattr(parameter, "dependencyParameters", None)),
            "dependents": names(getattr(parameter, "dependentParameters", None)),
        })
    return rows


def timeline_evidence(design):
    rows = []
    for index in range(design.timeline.count):
        item = design.timeline.item(index)
        entity = item.entity
        rows.append({
            "index": index, "name": item.name, "type": entity.objectType.split("::")[-1] if entity else None,
            "suppressed": item.isSuppressed, "rolled_back": item.isRolledBack, "health": health(item),
        })
    return rows


def measure(document, label):
    design = design_of(document)
    sketches = design.rootComponent.sketches
    return {
        "label": label,
        "document_units": design.fusionUnitsManager.distanceDisplayUnits,
        "design_type": "parametric" if design.designType == adsk.fusion.DesignTypes.ParametricDesignType else "direct",
        "feature_tree": timeline_evidence(design),
        "sketches": [sketch_evidence(sketches.item(index)) for index in range(sketches.count)],
        "parameters": parameter_evidence(design),
        **body_evidence(design),
    }


def export(document, path, saves):
    design = design_of(document)
    options = design.exportManager.createFusionArchiveExportOptions(str(path))
    if not design.exportManager.execute(options):
        raise RuntimeError("Fusion archive export failed: " + path.name)
    saves.append({"file": path.name, "sha256": digest(path), "size_bytes": path.stat().st_size})


def reopen(app, path, owned):
    options = app.importManager.createFusionArchiveImportOptions(str(path))
    document = app.importManager.importToNewDocument(options)
    if document is None:
        raise RuntimeError("Archive import did not return an owned new document: " + path.name)
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
        evidence["label"] = label
        evidence["file"] = CONTROL
        evidence["sha256"] = digest(repo / CONTROL)
        evidence["expected_volume_mm3"] = CONTROL_VOLUME_MM3
        evidence["healthy"] = evidence["body_count"] == 1 and abs(evidence["volume_mm3"] - CONTROL_VOLUME_MM3) <= max(1e-6, 1e-9 * CONTROL_VOLUME_MM3)
        return evidence
    finally:
        close(document, owned)


PLANES = {
    "XY": ("xYConstructionPlane", [(0, 0, 0), (40, 0, 0), (40, 20, 0), (0, 20, 0)]),
    "YZ": ("yZConstructionPlane", [(0, 0, 0), (0, 40, 0), (0, 40, 20), (0, 0, 20)]),
}


def sketch_point(sketch, world_mm):
    return sketch.modelToSketchSpace(adsk.core.Point3D.create(*(value / 10.0 for value in world_mm)))


def is_horizontal(line):
    start, end = line.startSketchPoint.geometry, line.endSketchPoint.geometry
    return abs(end.y - start.y) < 1e-9


def orient(line):
    orientations = adsk.fusion.DimensionOrientations
    return orientations.HorizontalDimensionOrientation if is_horizontal(line) else orientations.VerticalDimensionOrientation


def text_point(line, offset):
    start, end = line.startSketchPoint.geometry, line.endSketchPoint.geometry
    middle = adsk.core.Point3D.create((start.x + end.x) / 2.0, (start.y + end.y) / 2.0, 0)
    if is_horizontal(line):
        middle.y -= offset
    else:
        middle.x -= offset
    return middle


def build(app, plane):
    attribute, world = PLANES[plane]
    document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = design_of(document)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    root = design.rootComponent
    sketch = root.sketches.add(getattr(root, attribute))
    sketch.name = "RectangleSketch"
    corners = [sketch_point(sketch, vertex) for vertex in world]
    lines = sketch.sketchCurves.sketchLines
    bottom = lines.addByTwoPoints(corners[0], corners[1])
    right = lines.addByTwoPoints(bottom.endSketchPoint, corners[2])
    top = lines.addByTwoPoints(right.endSketchPoint, corners[3])
    left = lines.addByTwoPoints(top.endSketchPoint, bottom.startSketchPoint)
    constraints = sketch.geometricConstraints
    constraints.addCoincident(bottom.startSketchPoint, sketch.originPoint)
    for line in (bottom, right, top, left):
        if is_horizontal(line):
            constraints.addHorizontal(line)
        else:
            constraints.addVertical(line)
    dimensions = sketch.sketchDimensions
    width = dimensions.addDistanceDimension(bottom.startSketchPoint, bottom.endSketchPoint, orient(bottom), text_point(bottom, 0.8))
    height = dimensions.addDistanceDimension(left.startSketchPoint, left.endSketchPoint, orient(left), text_point(left, 0.8))
    width.parameter.name = "width_mm"
    width.parameter.expression = "40 mm"
    height.parameter.name = "height_mm"
    height.parameter.expression = "20 mm"
    design.computeAll()
    return document


def variant(app, document, label, file, saves, owned):
    export(document, file, saves)
    check = reopen(app, file, owned)
    try:
        design_of(check).computeAll()
        return {"label": label, "export": file.name, "before_save": measure(document, label), "reopened": measure(check, "fresh reopen of " + file.name)}
    finally:
        close(check, owned)


def edit_cycle(document, recipe, output, saves, observations, owned, app):
    design = design_of(document)
    for edit in recipe["independent_edits"]:
        name = edit["parameter"]
        parameter = design.allParameters.itemByName(name)
        if parameter is None:
            raise RuntimeError("Driving parameter is missing: " + name)
        original = parameter.expression
        parameter.expression = "{} mm".format(edit["value"])
        design.computeAll()
        edited = measure(document, "edit " + name + " = " + str(edit["value"]))
        edited["expected_area_mm2"] = edit["expected_area_mm2"]
        file = output / "P01-fusion-edit-{}-{}.f3d".format(name, edit["value"])
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
        observations.append({"edit": edit, "edited": edited, "export": file.name, "reopened": reopened, "restored": restored})


def run(context):
    app = adsk.core.Application.get()
    capture = Path(__file__).resolve().parent
    repo = capture.parents[3]
    specs = json.loads((repo / "re/automation/PairSpecs.json").read_text(encoding="utf-8"))
    recipe = next(item for item in specs["recipes"] if item["id"] == RECIPE_ID)
    output = capture / ("fusion-" + uuid.uuid4().hex[:12])
    output.mkdir()
    owned, saves, observations = [], [], {}
    result = {
        "recipe_id": RECIPE_ID, "application": "Autodesk Fusion", "exact_application_build": app.version,
        "authoring_recipe_sha256": hashlib.sha256(canonical(recipe)).hexdigest(),
        "specifications_sha256": digest(repo / "re/automation/PairSpecs.json"),
        "generator_sha256": digest(__file__),
        "authoring_origin": "Fusion API script authored from the P01 recipe; no Kit reader, writer or source archive used",
        "world_basis": "Fusion world XYZ; sketch on the XY construction plane with normal +Z",
        "configuration": "none", "saves": saves, "observations": observations, "errors": [],
        "limits": ["Repeat saves are separated by a document close and archive reopen in one Fusion process, not an application restart"],
    }
    try:
        observations["healthy_control_before"] = control_check(app, repo, owned, "before")
        document = build(app, "XY")
        owned.append(document)
        observations["baseline"] = measure(document, "baseline after build")
        export(document, output / "P01-fusion-baseline-a.f3d", saves)
        close(document, owned)
        document = reopen(app, output / "P01-fusion-baseline-a.f3d", owned)
        observations["fresh_reopen"] = measure(document, "fresh reopen of baseline-a")
        design_of(document).computeAll()
        observations["unchanged_rebuild"] = measure(document, "unchanged rebuild after reopen")
        export(document, output / "P01-fusion-baseline-b.f3d", saves)
        observations["edits"] = []
        edit_cycle(document, recipe, output, saves, observations["edits"], owned, app)
        design_of(document).fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.InchDistanceUnits
        design_of(document).computeAll()
        observations["units_inch"] = variant(app, document, "display units inches", output / "P01-fusion-units-inch.f3d", saves, owned)
        close(document, owned)
        document = build(app, "YZ")
        owned.append(document)
        observations["plane_yz"] = variant(app, document, "baseline reauthored on YZ", output / "P01-fusion-plane-yz.f3d", saves, owned)
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
        receipt = {"recipe_id": RECIPE_ID, "measurements": measurements.name, "measurement_receipt_sha256": digest(measurements),
                   "native_files": saves, "errors": len(result["errors"])}
        (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (output / "complete.txt").write_text("P01 Fusion capture finished; consult measurements.json errors.\n", encoding="utf-8")
