"""Small local patch, offset, stitch, unstitch and normal/deletion examples."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("surfacetools-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    cases = ("patch_rectangle", "patch_circle", "offset_positive", "offset_negative", "offset_rounded",
             "stitch_tight", "stitch_loose", "unstitch_face", "unstitch_chain", "reverse_normal", "delete_opening")
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            settings, sheets = {}, []
            for index in range(2 if case.startswith("stitch") else 1):
                sketch = root.sketches.add(root.xYConstructionPlane)
                if case == "patch_circle":
                    sketch.sketchCurves.sketchCircles.addByCenterRadius(point(1, 1, 0), 1.)
                else:
                    sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(2*index, 0, 0), point(2*index+2, 2, 0))
                if case.startswith("unstitch") or case == "delete_opening":
                    seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("20 mm"),
                                                                 adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                else:
                    inputs = root.features.patchFeatures.createInput(sketch.profiles.item(0),
                                                                     adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                    seed = root.features.patchFeatures.add(inputs)
                sheets.append(seed.bodies.item(0))
            if case.startswith("patch"):
                feature = seed
                settings.update(operation="NewBody", boundary_curve_count=1 if case == "patch_circle" else 4,
                                is_group_edges=inputs.isGroupEdges, group_continuity=inputs.groupContinuity,
                                group_weight=inputs.groupWeight, group_direction_flipped=inputs.groupIsContinuityDirectionFlipped)
            elif case.startswith("offset"):
                entities = adsk.core.ObjectCollection.create()
                entities.add(sheets[0].faces.item(0))
                inputs = root.features.offsetFeatures.createInput(entities, value("-3 mm" if case == "offset_negative" else "4 mm"),
                                                                 adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                                                                 case != "offset_negative")
                if case == "offset_rounded":
                    inputs.offsetType = adsk.fusion.OffsetTypes.RoundedOffsetType
                settings["offset_type"] = inputs.offsetType
                feature = root.features.offsetFeatures.add(inputs)
                settings.update(distance_cm=feature.distance.value, is_chain_selection=feature.isChainSelection,
                                operation="NewBody", selected_item_count=1)
            elif case.startswith("stitch"):
                entities = adsk.core.ObjectCollection.create()
                for sheet in sheets:
                    entities.add(sheet)
                inputs = root.features.stitchFeatures.createInput(entities, value("0.05 mm" if case == "stitch_loose" else "0.01 mm"))
                feature = root.features.stitchFeatures.add(inputs)
                settings.update(tolerance_cm=feature.tolerance.value, selected_item_count=2)
            elif case.startswith("unstitch"):
                entities = adsk.core.ObjectCollection.create()
                entities.add(seed.endFaces.item(0))
                chain = case == "unstitch_chain"
                feature = root.features.unstitchFeatures.add(entities, chain)
                settings.update(is_chain_selection=chain, selected_item_count=1)
            elif case == "reverse_normal":
                entities = adsk.core.ObjectCollection.create()
                entities.add(sheets[0])
                before = sheets[0].faces.item(0).geometry.normal.asArray()
                feature = root.features.reverseNormalFeatures.add(entities)
                settings.update(selected_item_count=1, input_plane_normal=before)
            else:
                feature = root.features.surfaceDeleteFaceFeatures.add(seed.endFaces.item(0))
                settings["selected_item_count"] = 1
            feature.name = "ProbeSurfaceTool"
            design.computeAll()
            settings.update(result_body_count=root.bRepBodies.count,
                            result_solids=[b.isSolid for b in root.bRepBodies])
            sample = {"file": case+".f3d", "kind": feature.objectType.split("::")[-1], "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Surface tool export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Surface tool exports finished; consult errors.\n")
