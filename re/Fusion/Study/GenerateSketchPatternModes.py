"""Capture broader study-owned native sketch pattern inputs and API evidence."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("circular_two_circles", "circular_line_circle", "circular_line", "circular_suppressed",
         "rectangular_two_circles", "rectangular_line_circle", "rectangular_direction", "rectangular_suppressed")


def entity_evidence(entity):
    result = {"type": entity.objectType, "is_valid": entity.isValid,
              "entity_token": entity.entityToken}
    try:
        result.update(is_reference=entity.isReference, is_fixed=entity.isFixed)
        line, circle = adsk.fusion.SketchLine.cast(entity), adsk.fusion.SketchCircle.cast(entity)
        if line:
            result.update(start_cm=line.startSketchPoint.geometry.asArray(),
                          end_cm=line.endSketchPoint.geometry.asArray(), is_construction=line.isConstruction)
        elif circle:
            result.update(center_cm=circle.centerSketchPoint.geometry.asArray(), radius_cm=circle.radius,
                          is_construction=circle.isConstruction)
    except RuntimeError as error:
        result["geometry_getter_error"] = str(error)
    return result


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("sketchpatternmodes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "token_scope": "Opaque SDK entity tokens retained for source evidence only; strings are not compared or decoded as native IDs."}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    cases = context.get("cases", CASES) if isinstance(context, dict) else CASES
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "ProbeSketchPattern"
            curves, constraints = sketch.sketchCurves, sketch.geometricConstraints
            if case.endswith("line") or "line_circle" in case:
                line = curves.sketchLines.addByTwoPoints(point(1.6, 2., 0), point(2.8, 2.4, 0))
                seeds = [line]
                if "line_circle" in case:
                    seeds.append(curves.sketchCircles.addByCenterRadius(point(2., 1., 0), .3))
            else:
                seeds = [curves.sketchCircles.addByCenterRadius(point(2., 1., 0), .3)]
                if "two_circles" in case:
                    seeds.append(curves.sketchCircles.addByCenterRadius(point(2., 2., 0), .2))
            if case.startswith("circular"):
                inputs = constraints.createCircularPatternInput(seeds, sketch.originPoint)
                inputs.quantity, inputs.totalAngle = value("4"), value("180 deg")
                constraint = constraints.addCircularPattern(inputs)
                settings = {"quantity": constraint.quantity.value, "total_angle_radians": constraint.totalAngle.value,
                            "is_symmetric": constraint.isSymmetric,
                            "center_cm": constraint.centerPoint.geometry.asArray()}
                requested_suppression = [False, True, False] if case.endswith("suppressed") else None
            else:
                inputs = constraints.createRectangularPatternInput(seeds, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
                inputs.quantityOne, inputs.quantityTwo = value("3"), value("2")
                inputs.distanceOne, inputs.distanceTwo = value("20 mm"), value("15 mm")
                if case.endswith("direction"):
                    direction_one = curves.sketchLines.addByTwoPoints(point(0, 0, 0), point(2., 1., 0))
                    direction_two = curves.sketchLines.addByTwoPoints(point(0, 0, 0), point(-1., 2., 0))
                    direction_one.isConstruction, direction_two.isConstruction = True, True
                    if not inputs.setDirectionOne(direction_one, value("3"), value("20 mm")):
                        raise RuntimeError("First direction input rejected")
                    if not inputs.setDirectionTwo(direction_two, value("2"), value("15 mm")):
                        raise RuntimeError("Second direction input rejected")
                constraint = constraints.addRectangularPattern(inputs)
                settings = {"quantity_one": constraint.quantityOne.value, "quantity_two": constraint.quantityTwo.value,
                            "distance_one_cm": constraint.distanceOne.value, "distance_two_cm": constraint.distanceTwo.value,
                            "distance_type": constraint.distanceType,
                            "symmetric_one": constraint.isSymmetricInDirectionOne, "symmetric_two": constraint.isSymmetricInDirectionTwo,
                            "direction_one": entity_evidence(constraint.directionOneEntity) if constraint.directionOneEntity else None,
                            "direction_two": entity_evidence(constraint.directionTwoEntity) if constraint.directionTwoEntity else None}
                requested_suppression = [False, True, False, False, False] if case.endswith("suppressed") else None
            if requested_suppression is not None:
                constraint.isSuppressed = requested_suppression
            settings.update(requested_suppression=requested_suppression, is_suppressed=list(constraint.isSuppressed),
                            entities=[entity_evidence(entity) for entity in constraint.entities],
                            created_entities=[entity_evidence(entity) for entity in constraint.createdEntities])
            sample = {"file": case+".f3d", "kind": constraint.objectType, "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit}
                                     for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Sketch pattern export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Sketch pattern modes finished; consult errors.\n")
