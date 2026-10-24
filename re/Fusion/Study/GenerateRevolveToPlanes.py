"""Observed one/two-sided revolve-to-construction-plane inputs."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("revolveto-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in ("positive_plane", "negative_plane", "two_planes"):
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, 1, 0), point(3, 4, 0))
            planes = []
            for angle in ([45, -35] if case == "two_planes" else [-35] if case == "negative_plane" else [45]):
                inputs = root.constructionPlanes.createInput()
                inputs.setByAngle(root.yConstructionAxis, value(str(angle)+" deg"), root.xYConstructionPlane)
                plane = root.constructionPlanes.add(inputs)
                plane.name = "ToPlane"+str(angle)
                planes.append(plane)
            inputs = root.features.revolveFeatures.createInput(sketch.profiles.item(0), root.yConstructionAxis,
                                                               adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            if case == "two_planes":
                success = inputs.setTwoSideToExtent(planes[0], planes[1])
            elif case == "negative_plane":
                success = inputs.setOneSideToExtent(planes[0], adsk.core.Vector3D.create(0, 0, 1))
            else:
                success = inputs.setOneSideToExtent(planes[0])
            if not success:
                raise RuntimeError("To-plane revolve input rejected")
            feature = root.features.revolveFeatures.add(inputs)
            feature.name = "ProbeRevolveTo"
            design.computeAll()
            sample = {"file": case+".f3d", "extent_kind": feature.extentDefinition.objectType.split("::")[-1],
                      "input_planes": [{"name": p.name, "origin_cm": p.geometry.origin.asArray(),
                                        "normal": p.geometry.normal.asArray()} for p in planes],
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            options = design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Revolve-to export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Revolve-to exports finished; consult errors.\n")
