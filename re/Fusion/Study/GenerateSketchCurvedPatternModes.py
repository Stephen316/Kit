"""Owned curved sketch-pattern samples; current API supports sketch curves.

Preserves explicit entities/createdEntities order and per-entity constraints.
Geometry is supporting API evidence, never an inferred instance identity.
"""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("circular_arc", "rectangular_arc", "circular_ellipse",
         "rectangular_ellipse", "rectangular_fitted_spline")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("sketchcurvedpatterns-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {
        "fusion_version": app.version, "samples": [], "errors": [],
        "sdk_scope": "GeometricConstraints.createCircularPatternInput/createRectangularPatternInput accept same-sketch curves; createdEntities excludes input entities",
        "identity_scope": "API tokens retained as opaque evidence; entity relationships and result order come from actual getters, never coordinate matching",
        "unsupported_scope": ["pattern suppression not varied", "custom pattern directions not varied", "mixed curved seeds not captured"],
    }
    cases = [case for case in CASES if not isinstance(context, dict)
             or "cases" not in context or case in context["cases"]]
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString

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
        for key, field in (("is_reference", "isReference"), ("is_fixed", "isFixed"),
                           ("is_construction", "isConstruction"), ("is_2d", "is2D")):
            result[key] = observe(field, lambda field=field: getattr(entity, field), errors)
        result["sketch_name"] = observe("parentSketch.name", lambda: entity.parentSketch.name, errors)
        attached = observe("geometricConstraints", lambda: collection(entity.geometricConstraints), errors)
        result["attached_constraints"] = [identity(item) for item in attached] if attached is not None else None
        arc = adsk.fusion.SketchArc.cast(entity)
        ellipse = adsk.fusion.SketchEllipse.cast(entity)
        spline = adsk.fusion.SketchFittedSpline.cast(entity)
        if arc or spline:
            for end in ("start", "end"):
                vertex = observe(end+"SketchPoint", lambda end=end: getattr(entity, end+"SketchPoint"), errors)
                result[end+"_point"] = point_truth(vertex) if vertex else None
        if arc or ellipse:
            center = observe("centerSketchPoint", lambda: entity.centerSketchPoint, errors)
            result["center_point"] = point_truth(center) if center else None
        if arc:
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
        try:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "CurvedPatternProbe"
            curves, constraints = sketch.sketchCurves, sketch.geometricConstraints
            if case.endswith("arc"):
                seed = curves.sketchArcs.addByCenterStartSweep(point(2., 1., 0), point(2.45, 1., 0), 1.2)
            elif case.endswith("ellipse"):
                seed = curves.sketchEllipses.add(point(2., 1., 0), point(2.6, 1., 0), point(2., 1.25, 0))
            else:
                fit_points = adsk.core.ObjectCollection.create()
                for coords in ((1.4, 1., 0), (1.7, 1.6, 0), (2.3, 1.2, 0), (2.6, 1.7, 0)):
                    fit_points.add(point(*coords))
                seed = curves.sketchFittedSplines.add(fit_points)
            if seed is None:
                raise RuntimeError("Curved seed creation returned None")
            before = entity_truth(seed)
            if case.startswith("circular"):
                requested = {"quantity": 3, "total_angle_expression": "120 deg", "is_symmetric": False,
                             "center_point": point_truth(sketch.originPoint)}
                inputs = constraints.createCircularPatternInput([seed], sketch.originPoint)
                inputs.quantity, inputs.totalAngle, inputs.isSymmetric = value("3"), value("120 deg"), False
                pattern = constraints.addCircularPattern(inputs)
                parameter_fields = ("quantity", "totalAngle")
                scalar_fields = (("is_symmetric", "isSymmetric"),)
            else:
                requested = {"quantity_one": 2, "quantity_two": 2, "distance_one_expression": "20 mm",
                             "distance_two_expression": "15 mm", "distance_type": adsk.fusion.PatternDistanceType.SpacingPatternDistanceType,
                             "symmetric_one": False, "symmetric_two": False}
                inputs = constraints.createRectangularPatternInput([seed], requested["distance_type"])
                inputs.quantityOne, inputs.quantityTwo = value("2"), value("2")
                inputs.distanceOne, inputs.distanceTwo = value("20 mm"), value("15 mm")
                inputs.isSymmetricInDirectionOne, inputs.isSymmetricInDirectionTwo = False, False
                pattern = constraints.addRectangularPattern(inputs)
                parameter_fields = ("quantityOne", "quantityTwo", "distanceOne", "distanceTwo")
                scalar_fields = (("distance_type", "distanceType"), ("symmetric_one", "isSymmetricInDirectionOne"),
                                 ("symmetric_two", "isSymmetricInDirectionTwo"))
            if pattern is None:
                raise RuntimeError("Curved sketch pattern creation returned None")
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
            file = case + ".f3d"
            design.timeline.moveToEnd()
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output / file))):
                raise RuntimeError("Curved sketch pattern local export failed")
            truth["samples"].append({"file": file, "requested": requested, "seed_before_pattern": before, "settings": settings})
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    truth["errors"].append({"case": case, "cleanup": "timeline restore", "error": traceback.format_exc()})
            if doc is not None:
                try:
                    doc.close(False)
                except Exception:
                    truth["errors"].append({"case": case, "cleanup": "owned document close(False)", "error": traceback.format_exc()})
            (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output / "complete.txt").write_text("Curved sketch pattern generation finished; consult errors.\n")
