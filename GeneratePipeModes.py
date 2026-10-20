"""Controlled pipe sections, hollow thickness and open/closed path fractions."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("pipemodes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in ("circular", "square", "triangular", "hollow", "partial_open", "partial_closed"):
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            if case == "partial_closed":
                curve = sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 3.)
            else:
                curve = sketch.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(6, 0, 0))
            path = root.features.createPath(curve, False)
            inputs = root.features.pipeFeatures.createInput(path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            inputs.sectionType = {"square": adsk.fusion.PipeSectionTypes.SquarePipeSectionType,
                                  "triangular": adsk.fusion.PipeSectionTypes.TriangularPipeSectionType}.get(case, adsk.fusion.PipeSectionTypes.CircularPipeSectionType)
            inputs.sectionSize = value("8 mm" if case == "square" else "6 mm")
            if case == "hollow":
                inputs.sectionThickness = value("0.8 mm")
            if case.startswith("partial"):
                inputs.distanceOne = value("0.6" if case == "partial_open" else "0.45")
            if case == "partial_closed":
                inputs.distanceTwo = value("0.2")
            feature = root.features.pipeFeatures.add(inputs)
            feature.name = "ProbePipe"
            settings = {"section_type": feature.sectionType, "section_size_cm": feature.sectionSize.value,
                        "is_hollow": feature.isHollow,
                        "section_thickness_cm": feature.sectionThickness.value if feature.sectionThickness else None,
                        "distance_one": feature.distanceOne.value,
                        "distance_two": feature.distanceTwo.value if feature.distanceTwo else None,
                        "path_is_closed": case == "partial_closed", "operation": "NewBody"}
            sample = {"file": case+".f3d", "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Pipe export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Pipe exports finished; consult errors.\n")
