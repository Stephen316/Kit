"""Observed sketch offset and pattern constraints with API geometry evidence."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ("OffsetLinePositive", "OffsetLineNegative", "OffsetRectangle", "OffsetCircle",
         "RectangularSpacing", "RectangularExtent", "RectangularSymmetric",
         "CircularPartial", "CircularFull", "CircularSymmetric")


def curve_evidence(curve):
    kind = curve.objectType.split("::")[-1]
    item = {"kind": kind}
    if kind == "SketchLine":
        item.update(start=curve.startSketchPoint.geometry.asArray(), end=curve.endSketchPoint.geometry.asArray())
    elif kind == "SketchCircle":
        item.update(center=curve.centerSketchPoint.geometry.asArray(), radius=curve.radius)
    return item


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("sketchtools-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        for case in CASES:
            try:
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.name = case
                constraints, curves = sketch.geometricConstraints, sketch.sketchCurves
                if case.startswith("Offset"):
                    if case == "OffsetRectangle":
                        parents = list(curves.sketchLines.addTwoPointRectangle(point(1, 1, 0), point(4, 3, 0)))
                    elif case == "OffsetCircle":
                        parents = [curves.sketchCircles.addByCenterRadius(point(2, 1, 0), 1.)]
                    else:
                        parents = [curves.sketchLines.addByTwoPoints(point(1, 1, 0), point(4, 1, 0))]
                    inputs = constraints.createOffsetInput(parents, value("-3 mm" if case.endswith("Negative") else "3 mm"))
                    inputs.isTopologyMatched = True
                    constraint = constraints.addOffset2(inputs)
                    settings = {"distance_cm": constraint.distance, "topology_matched": constraint.isTopologyMatched,
                                "parent_curves": [curve_evidence(c) for c in constraint.parentCurves],
                                "child_curves": [curve_evidence(c) for c in constraint.childCurves],
                                "dimension_kind": constraint.dimension.objectType.split("::")[-1],
                                "parameter_name": constraint.dimension.parameter.name,
                                "parameter_value": constraint.dimension.parameter.value}
                else:
                    source = curves.sketchCircles.addByCenterRadius(point(2, 1, 0), .3)
                    if case.startswith("Rectangular"):
                        inputs = constraints.createRectangularPatternInput([source],
                            adsk.fusion.PatternDistanceType.ExtentPatternDistanceType if case.endswith("Extent")
                            else adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
                        # The SDK documents nullable direction arguments, but this
                        # build rejects None in setDirectionOne. Keep default axes
                        # and assign the numeric input properties directly.
                        inputs.quantityOne, inputs.distanceOne = value("3"), value("20 mm")
                        inputs.quantityTwo, inputs.distanceTwo = value("2"), value("15 mm")
                        inputs.isSymmetricInDirectionOne = case.endswith("Symmetric")
                        constraint = constraints.addRectangularPattern(inputs)
                        settings = {"quantity_one": constraint.quantityOne.value, "quantity_two": constraint.quantityTwo.value,
                                    "distance_one_cm": constraint.distanceOne.value, "distance_two_cm": constraint.distanceTwo.value,
                                    "distance_type": constraint.distanceType,
                                    "symmetric_one": constraint.isSymmetricInDirectionOne,
                                    "symmetric_two": constraint.isSymmetricInDirectionTwo}
                    else:
                        inputs = constraints.createCircularPatternInput([source], sketch.originPoint)
                        inputs.quantity = value("4")
                        inputs.totalAngle = value("360 deg" if case.endswith("Full") else "180 deg")
                        inputs.isSymmetric = case.endswith("Symmetric")
                        constraint = constraints.addCircularPattern(inputs)
                        settings = {"quantity": constraint.quantity.value, "total_angle_radians": constraint.totalAngle.value,
                                    "is_symmetric": constraint.isSymmetric, "center_cm": constraint.centerPoint.geometry.asArray()}
                    settings.update(entities=[curve_evidence(c) for c in constraint.entities],
                                    created_entities=[curve_evidence(c) for c in constraint.createdEntities],
                                    is_suppressed=constraint.isSuppressed)
                truth["samples"].append({"name": sketch.name, "kind": constraint.objectType.split("::")[-1],
                                         "settings": settings})
            except Exception:
                truth["errors"].append({"case": case, "error": traceback.format_exc()})
        options = design.exportManager.createFusionArchiveExportOptions(str(output/"sketchtools.f3d"))
        if not design.exportManager.execute(options):
            raise RuntimeError("Sketch tool export failed")
    except Exception:
        truth["errors"].append({"case": "export", "error": traceback.format_exc()})
    finally:
        doc.close(False)
        (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output/"complete.txt").write_text("Sketch tool export finished; consult errors.\n")
