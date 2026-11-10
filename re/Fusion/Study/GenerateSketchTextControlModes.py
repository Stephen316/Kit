"""Eight owned rectangle SketchText control contrasts against the captured plain baseline.

Run only through the coordinated Fusion dispatcher. Exports are local; each newly
created document is closed without saving. Existing user documents are untouched.
"""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("horizontal_flip", "vertical_flip", "bold_italic", "underline",
         "center", "middle", "right_bottom", "spacing")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("sketchtextcontrols-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {
        "fusion_version": app.version, "samples": [], "errors": [],
        "sdk_methods": {
            "creation": "SketchTexts.createInput3(expression, ValueInput)",
            "layout": "SketchTextInput.setAsMultiLine",
            "content": "SketchText.textParameter.textValue/expression",
            "height": "SketchText.heightParameter.value/expression",
            "note": "Installed SDK defines createInput3, not createInput2. Single-line cases use a rectangle containing one line.",
        },
        "scope": {
            "captured": ["horizontal flip", "vertical flip", "bold+italic", "underline", "horizontal center/right alignment", "vertical middle/bottom alignment", "character spacing25%"],
            "not_varied": ["content", "height", "font", "rotation", "font fallback"],
            "baseline": "sketchtexts-a16af12c28bf/plain.f3d",
            "contrast_note": "center changes only horizontal alignment; middle changes only vertical alignment; right_bottom supplies level2 for both independently located fields.",
            "not_captured": ["along-path text", "fit-on-path text", "parameter expressions combining numeric/text values"],
        },
        "token_scope": "Opaque API tokens are retained without native object ID interpretation",
    }
    selected = [case for case in CASES if not isinstance(context, dict)
                or "cases" not in context or case in context["cases"]]
    point = adsk.core.Point3D.create

    def observe(label, read, errors):
        try:
            return read()
        except Exception:
            errors.append({"getter": label, "error": traceback.format_exc()})
            return None

    def identity(entity):
        if entity is None:
            return None
        errors = []
        return {
            "kind": observe("objectType", lambda: entity.objectType.split("::")[-1], errors),
            "entity_token": observe("entityToken", lambda: entity.entityToken, errors),
            "getter_errors": errors,
        }

    def parameter_truth(parameter, is_text):
        if parameter is None:
            return None
        errors = []
        result = {"identity": identity(parameter), "getter_errors": errors}
        for field in ("name", "role", "expression", "unit"):
            result[field] = observe(field, lambda field=field: getattr(parameter, field), errors)
        field = "textValue" if is_text else "value"
        result["text_value" if is_text else "value_cm"] = observe(field, lambda: getattr(parameter, field), errors)
        return result

    def line_truth(line):
        errors = []
        result = {"identity": identity(line), "getter_errors": errors}
        for key, field in (("is_reference", "isReference"), ("is_fixed", "isFixed"),
                           ("is_construction", "isConstruction"), ("is_2d", "is2D")):
            result[key] = observe(field, lambda field=field: getattr(line, field), errors)
        for end in ("start", "end"):
            sketch_point = observe(end + "SketchPoint", lambda end=end: getattr(line, end + "SketchPoint"), errors)
            result[end + "_point"] = identity(sketch_point)
            result[end + "_sketch_cm"] = observe(end + "SketchPoint.geometry", lambda: sketch_point.geometry.asArray(), errors)
            result[end + "_world_cm"] = observe(end + "SketchPoint.worldGeometry", lambda: sketch_point.worldGeometry.asArray(), errors)
        return result

    def definition_truth(definition):
        if definition is None:
            return None
        errors = []
        result = {"kind": observe("objectType", lambda: definition.objectType.split("::")[-1], errors),
                  "getter_errors": errors}
        for key, field in (("horizontal_alignment", "horizontalAlignment"),
                           ("vertical_alignment", "verticalAlignment"),
                           ("character_spacing_percent", "characterSpacing")):
            result[key] = observe(field, lambda field=field: getattr(definition, field), errors)
        rectangle = observe("rectangleLines", lambda: definition.rectangleLines, errors)
        result["rectangle_lines"] = [line_truth(line) for line in rectangle] if rectangle is not None else None
        return result

    for case in selected:
        doc, design = None, None
        try:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            sketch = design.rootComponent.sketches.add(design.rootComponent.xYConstructionPlane)
            sketch.name = "SketchTextProbe"
            content, height = "KIT", "5 mm"
            style = ((adsk.fusion.TextStyles.TextStyleBold | adsk.fusion.TextStyles.TextStyleItalic)
                     if case == "bold_italic" else adsk.fusion.TextStyles.TextStyleUnderline
                     if case == "underline" else 0)
            requested = {
                "text": content, "height_expression": height, "font_name": "Arial", "text_style": style,
                "is_horizontal_flip": False, "is_vertical_flip": False,
                "layout": "MultiLineTextDefinition", "corner_sketch_cm": [1., 1., 0.],
                "diagonal_sketch_cm": [9., 4., 0.], "horizontal_alignment": adsk.core.HorizontalAlignments.LeftHorizontalAlignment,
                "vertical_alignment": adsk.core.VerticalAlignments.TopVerticalAlignment, "character_spacing_percent": 0.,
            }
            if case == "horizontal_flip":
                requested["is_horizontal_flip"] = True
            elif case == "vertical_flip":
                requested["is_vertical_flip"] = True
            elif case == "center":
                requested["horizontal_alignment"] = adsk.core.HorizontalAlignments.CenterHorizontalAlignment
            elif case == "middle":
                requested["vertical_alignment"] = adsk.core.VerticalAlignments.MiddleVerticalAlignment
            elif case == "right_bottom":
                requested["horizontal_alignment"] = adsk.core.HorizontalAlignments.RightHorizontalAlignment
                requested["vertical_alignment"] = adsk.core.VerticalAlignments.BottomVerticalAlignment
            elif case == "spacing":
                requested["character_spacing_percent"] = 25.
            inputs = sketch.sketchTexts.createInput3("'KIT'", adsk.core.ValueInput.createByString(height))
            if inputs is None:
                raise RuntimeError("SketchTexts.createInput3 returned None")
            # The documented literal setter avoids treating a newline as a text-expression escape.
            inputs.text = content
            inputs.fontName = requested["font_name"]
            inputs.textStyle = style
            inputs.isHorizontalFlip = requested["is_horizontal_flip"]
            inputs.isVerticalFlip = requested["is_vertical_flip"]
            if not inputs.setAsMultiLine(point(*requested["corner_sketch_cm"]), point(*requested["diagonal_sketch_cm"]),
                                         requested["horizontal_alignment"], requested["vertical_alignment"],
                                         requested["character_spacing_percent"]):
                raise RuntimeError("SketchTextInput.setAsMultiLine returned False")
            input_errors = []
            input_truth = {"getter_errors": input_errors}
            for field in ("text", "expression", "fontName", "textStyle", "isHorizontalFlip", "isVerticalFlip"):
                input_truth[field] = observe(field, lambda field=field: getattr(inputs, field), input_errors)
            text = sketch.sketchTexts.add(inputs)
            if text is None:
                raise RuntimeError("SketchTexts.add returned None")
            design.timeline.moveToEnd()
            errors = []
            settings = {"identity": identity(text), "getter_errors": errors,
                        "sketch_name": sketch.name, "sketch_identity": identity(sketch)}
            for key, field in (("font_name", "fontName"), ("text_style", "textStyle"),
                               ("is_horizontal_flip", "isHorizontalFlip"), ("is_vertical_flip", "isVerticalFlip"),
                               ("is_reference", "isReference"), ("is_fixed", "isFixed"), ("is_2d", "is2D")):
                settings[key] = observe(field, lambda field=field: getattr(text, field), errors)
            text_parameter = observe("textParameter", lambda: text.textParameter, errors)
            height_parameter = observe("heightParameter", lambda: text.heightParameter, errors)
            settings["text_parameter"] = parameter_truth(text_parameter, True)
            settings["height_parameter"] = parameter_truth(height_parameter, False)
            settings["definition"] = definition_truth(observe("definition", lambda: text.definition, errors))
            settings["sketch_to_world_matrix"] = observe("sketch.transform", lambda: sketch.transform.asArray(), errors)
            bounds = observe("boundingBox", lambda: text.boundingBox, errors)
            settings["bounding_box_cm"] = observe("boundingBox.points", lambda: [bounds.minPoint.asArray(), bounds.maxPoint.asArray()], errors) if bounds else None
            curves = observe("asCurves", lambda: text.asCurves(), errors)
            settings["outline_curve_count"] = len(curves) if curves is not None else None
            settings["outline_curve_types"] = sorted(set(curve.objectType.split("::")[-1] for curve in curves)) if curves is not None else None
            settings["sketch_text_count"] = observe("sketchTexts.count", lambda: sketch.sketchTexts.count, errors)
            file = case + ".f3d"
            design.timeline.moveToEnd()
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output / file))):
                raise RuntimeError("SketchText local export failed")
            truth["samples"].append({"file": file, "requested": requested, "input": input_truth, "settings": settings})
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
    (output / "complete.txt").write_text("SketchText control generation finished; consult errors.\n")
