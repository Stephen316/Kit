"""Independent journaled symmetric-pattern index contrasts and two held-out cases.

Preserves explicit entities/createdEntities order and per-entity constraints.
Geometry is supporting API evidence, never an inferred instance identity.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CONFIGS = {
    "circular_odd_low": {"stage": "discovery", "quantity": 5, "suppressed_api_indices": [0]},
    "circular_even_high": {"stage": "discovery", "quantity": 6, "suppressed_api_indices": [4]},
    "rectangular_first_even": {"stage": "discovery", "quantity_one": 4, "quantity_two": 2,
                               "symmetric_one": True, "symmetric_two": False, "suppressed_api_indices": [0]},
    "rectangular_second_odd": {"stage": "discovery", "quantity_one": 2, "quantity_two": 3,
                               "symmetric_one": False, "symmetric_two": True, "suppressed_api_indices": [1]},
    "circular_odd_holdout": {"stage": "holdout", "quantity": 7, "suppressed_api_indices": [4]},
    "rectangular_both_holdout": {"stage": "holdout", "quantity_one": 3, "quantity_two": 4,
                                 "symmetric_one": True, "symmetric_two": True, "suppressed_api_indices": [0, 10]},
}
CASES = tuple(case for case, config in CONFIGS.items() if config["stage"] == "discovery")



def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("sketchsymmetricindices-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {
        "fusion_version": app.version, "samples": [], "errors": [],
        "sdk_scope": "Pattern inputs accept same-sketch points/curves; suppression excludes the seed; rectangular directionTwo defaults perpendicular to directionOne",
        "prepared_status": "Prepared and uncaptured; no general native suppression-index rule claimed",
        "case_plan": CONFIGS,
        "native_id_scope": "Only offline exported native records establish native IDs; API tokens remain opaque",
        "identity_scope": "API tokens retained as opaque evidence; entity relationships and result order come from actual getters, never coordinate matching",
        "unsupported_scope": ["Only six prepared probes; no new native rule is supported until actual captures and holdouts agree", "Full-circle, negative-angle and mixed-curved symmetric suppression remain outside this batch"],
    }
    requested_cases = context.get("cases", CASES) if isinstance(context, dict) else CASES
    cases = [case for case in CONFIGS if case in requested_cases]
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString

    def journal(phase, case=None, **fields):
        event = {"time_utc": datetime.now(timezone.utc).isoformat(), "phase": phase,
                 "case": case, "completed_sample_count": len(truth["samples"]),
                 "error_count": len(truth["errors"]), **fields}
        with (output / "journal.jsonl").open("a") as stream:
            stream.write(json.dumps(event) + "\n")
        (output / "progress.json").write_text(json.dumps(event, indent=2))
        (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))

    journal("batch_begin", selected_cases=cases)

    def observe(name, read, errors):
        try:
            return read()
        except Exception:
            errors.append({"getter": name, "error": traceback.format_exc()})
            return None

    def identity(entity):
        if entity is None:
            return None
        errors = []
        return {"type": observe("objectType", lambda: entity.objectType, errors),
                "entity_token": observe("entityToken", lambda: entity.entityToken, errors),
                "is_valid": observe("isValid", lambda: entity.isValid, errors), "getter_errors": errors}

    def serializable(value):
        if value is None or isinstance(value, (str, bool, int, float)):
            return value
        if isinstance(value, (list, tuple)):
            return [serializable(item) for item in value]
        if hasattr(value, "asArray"):
            return value.asArray()
        # Fusion also returns SWIG Point3DVector/DoubleVector containers.
        return [serializable(item) for item in value]

    def collection(collection):
        return [collection.item(i) for i in range(collection.count)]

    def point_truth(vertex):
        errors = []
        return {"identity": identity(vertex),
                "sketch_cm": observe("geometry", lambda: vertex.geometry.asArray(), errors),
                "world_cm": observe("worldGeometry", lambda: vertex.worldGeometry.asArray(), errors),
                "getter_errors": errors}

    def entity_truth(entity):
        if entity is None:
            return None
        errors = []
        result = {"identity": identity(entity), "getter_errors": errors}
        vertex = adsk.fusion.SketchPoint.cast(entity)
        fields = [("is_reference", "isReference"), ("is_fixed", "isFixed"), ("is_2d", "is2D")]
        if not vertex:
            fields.append(("is_construction", "isConstruction"))
        for key, field in fields:
            result[key] = observe(field, lambda field=field: getattr(entity, field), errors)
        result["sketch_name"] = observe("parentSketch.name", lambda: entity.parentSketch.name, errors)
        attached = observe("geometricConstraints", lambda: collection(entity.geometricConstraints), errors)
        result["attached_constraints"] = [identity(item) for item in attached] if attached is not None else None
        if vertex:
            result["point"] = point_truth(vertex)
            return result
        arc = adsk.fusion.SketchArc.cast(entity)
        ellipse = adsk.fusion.SketchEllipse.cast(entity)
        spline = adsk.fusion.SketchFittedSpline.cast(entity)
        circle = adsk.fusion.SketchCircle.cast(entity)
        line = adsk.fusion.SketchLine.cast(entity)
        if arc or spline or line:
            for end in ("start", "end"):
                vertex = observe(end+"SketchPoint", lambda end=end: getattr(entity, end+"SketchPoint"), errors)
                result[end+"_point"] = point_truth(vertex) if vertex else None
        if arc or ellipse or circle:
            center = observe("centerSketchPoint", lambda: entity.centerSketchPoint, errors)
            result["center_point"] = point_truth(center) if center else None
        if arc or circle:
            result["radius_cm"] = observe("radius", lambda: entity.radius, errors)
        if ellipse:
            for key, field in (("major_radius_cm", "majorAxisRadius"), ("minor_radius_cm", "minorAxisRadius")):
                result[key] = observe(field, lambda field=field: getattr(entity, field), errors)
            result["major_axis"] = observe("majorAxis", lambda: entity.majorAxis.asArray(), errors)
            result["major_axis_line"] = observe("majorAxisLine", lambda: identity(entity.majorAxisLine), errors)
            result["minor_axis_line"] = observe("minorAxisLine", lambda: identity(entity.minorAxisLine), errors)
        if spline:
            fit_points = observe("fitPoints", lambda: collection(spline.fitPoints), errors)
            result["fit_points"] = [point_truth(vertex) for vertex in fit_points] if fit_points is not None else None
            result["is_closed"] = observe("isClosed", lambda: spline.isClosed, errors)
        geometry = observe("geometry", lambda: entity.geometry, errors)
        if geometry:
            result["geometry_type"] = observe("geometry.objectType", lambda: geometry.objectType, errors)
            # Arc/Ellipse/NURBS getData schemas are defined by the actual geometry type.
            result["geometry_data_sketch_cm"] = observe("geometry.getData", lambda: serializable(geometry.getData()), errors)
        return result

    def parameter_truth(parameter):
        errors = []
        result = {"identity": identity(parameter), "getter_errors": errors}
        for field in ("name", "role", "value", "expression", "unit"):
            result[field] = observe(field, lambda field=field: getattr(parameter, field), errors)
        return result

    for case in cases:
        doc, design = None, None
        journal("case_begin", case)
        try:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            journal("document_created", case)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "SymmetricIndexProbe"
            curves, constraints = sketch.sketchCurves, sketch.geometricConstraints
            config = CONFIGS[case]
            seeds = [curves.sketchCircles.addByCenterRadius(point(2., 1., 0), .3)]
            if any(seed is None for seed in seeds):
                raise RuntimeError("Pattern gap seed creation returned None")
            before = [dict(api_order_index=i, **entity_truth(seed)) for i, seed in enumerate(seeds)]
            journal("seed_ready", case)
            input_errors = []
            input_settings = {"getter_errors": input_errors}
            if case.startswith("circular"):
                requested = {"stage": config["stage"], "quantity": config["quantity"],
                             "total_angle_expression": "180 deg", "is_symmetric": True,
                             "center_point": point_truth(sketch.originPoint)}
                inputs = constraints.createCircularPatternInput(seeds, sketch.originPoint)
                inputs.quantity, inputs.totalAngle = value(str(config["quantity"])), value("180 deg")
                inputs.isSymmetric = True
                journal("pattern_add_begin", case)
                pattern = constraints.addCircularPattern(inputs)
                parameter_fields = ("quantity", "totalAngle")
                scalar_fields = (("is_symmetric", "isSymmetric"),)
                requested_mask = [index in config["suppressed_api_indices"] for index in range(config["quantity"]-1)]
            else:
                requested = {"stage": config["stage"], "quantity_one": config["quantity_one"],
                             "quantity_two": config["quantity_two"], "distance_one_expression": "20 mm",
                             "distance_two_expression": "15 mm", "distance_type": adsk.fusion.PatternDistanceType.SpacingPatternDistanceType,
                             "symmetric_one": config["symmetric_one"], "symmetric_two": config["symmetric_two"],
                             "direction_two_setting": "Both directions left unset; default sketch axes"}
                inputs = constraints.createRectangularPatternInput(seeds, requested["distance_type"])
                inputs.quantityOne, inputs.quantityTwo = value(str(config["quantity_one"])), value(str(config["quantity_two"]))
                inputs.distanceOne, inputs.distanceTwo = value("20 mm"), value("15 mm")
                inputs.isSymmetricInDirectionOne = config["symmetric_one"]
                inputs.isSymmetricInDirectionTwo = config["symmetric_two"]
                for field in ("directionOneEntity", "directionTwoEntity"):
                    input_settings[field] = observe(field, lambda field=field: identity(getattr(inputs, field)), input_errors)
                journal("pattern_add_begin", case)
                pattern = constraints.addRectangularPattern(inputs)
                parameter_fields = ("quantityOne", "quantityTwo", "distanceOne", "distanceTwo")
                scalar_fields = (("distance_type", "distanceType"), ("symmetric_one", "isSymmetricInDirectionOne"),
                                 ("symmetric_two", "isSymmetricInDirectionTwo"))
                requested_mask = [index in config["suppressed_api_indices"] for index in range(config["quantity_one"]*config["quantity_two"]-1)]
            if pattern is None:
                raise RuntimeError("Pattern gap probe creation returned None")
            journal("pattern_created", case)
            pre_suppression = None
            if requested_mask is not None:
                pre_errors = []
                pre_entities = observe("createdEntities", lambda: list(pattern.createdEntities), pre_errors)
                pre_suppression = {"getter_errors": pre_errors,
                    "is_suppressed": observe("isSuppressed", lambda: list(pattern.isSuppressed), pre_errors),
                    "created_entities": [dict(api_order_index=i, **entity_truth(entity)) for i, entity in enumerate(pre_entities)] if pre_entities is not None else None}
                journal("suppression_set_begin", case, requested_mask=requested_mask)
                pattern.isSuppressed = requested_mask
                journal("suppression_set_complete", case)
            requested["is_suppressed"] = requested_mask
            requested["suppressed_api_indices"] = config["suppressed_api_indices"]
            design.timeline.moveToEnd()
            errors = []
            settings = {"identity": identity(pattern), "getter_errors": errors, "parameters": {}}
            for field in parameter_fields:
                parameter = observe(field, lambda field=field: getattr(pattern, field), errors)
                settings["parameters"][field] = parameter_truth(parameter) if parameter else None
            for key, field in scalar_fields:
                settings[key] = observe(field, lambda field=field: getattr(pattern, field), errors)
            settings["is_suppressed"] = observe("isSuppressed", lambda: list(pattern.isSuppressed), errors)
            for key, field in (("entities", "entities"), ("created_entities", "createdEntities")):
                entities = observe(field, lambda field=field: list(getattr(pattern, field)), errors)
                settings[key] = [dict(api_order_index=i, **entity_truth(entity)) for i, entity in enumerate(entities)] if entities is not None else None
            if case.startswith("circular"):
                center = observe("centerPoint", lambda: pattern.centerPoint, errors)
                settings["center_point"] = point_truth(center) if center else None
            else:
                for key, field in (("direction_one", "directionOneEntity"), ("direction_two", "directionTwoEntity")):
                    settings[key] = observe(field, lambda field=field: entity_truth(getattr(pattern, field)), errors)
            settings["all_sketch_constraints"] = observe("sketch.geometricConstraints", lambda: [identity(item) for item in collection(constraints)], errors)
            settings["all_model_parameters"] = observe("root.modelParameters", lambda: [parameter_truth(item) for item in collection(root.modelParameters)], errors)
            settings["input_direction_getters"] = input_settings
            settings["pre_suppression"] = pre_suppression
            file = case + ".f3d"
            journal("getters_captured", case)
            design.timeline.moveToEnd()
            journal("export_begin", case, file=file)
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output / file))):
                raise RuntimeError("Symmetric index probe local export failed")
            truth["samples"].append({"file": file, "requested": requested, "seeds_before_pattern": before, "settings": settings})
            journal("export_complete", case, file=file, size_bytes=(output / file).stat().st_size)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
            journal("case_error", case)
        finally:
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    truth["errors"].append({"case": case, "cleanup": "timeline restore", "error": traceback.format_exc()})
            if doc is not None:
                try:
                    doc.close(False)
                    journal("owned_document_closed_without_save", case)
                except Exception:
                    truth["errors"].append({"case": case, "cleanup": "owned document close(False)", "error": traceback.format_exc()})
            journal("case_finished", case)
    journal("batch_complete", selected_cases=cases)
    (output / "complete.txt").write_text("Symmetric index generation finished; consult errors.\n")
