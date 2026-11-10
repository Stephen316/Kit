"""Capture owned Combine inputs/controls without saving cloud documents."""
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ('combinemodes-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': []}
    op = adsk.fusion.FeatureOperations
    cases = [('join_keep', op.JoinFeatureOperation, True, False, False, False),
             ('join_consume', op.JoinFeatureOperation, False, False, False, False),
             ('cut_keep', op.CutFeatureOperation, True, False, False, False),
             ('intersect_keep', op.IntersectFeatureOperation, True, False, False, False),
             ('cut_multiple', op.CutFeatureOperation, True, True, False, False),
             ('cut_swapped', op.CutFeatureOperation, True, False, True, False),
             ('join_component', op.JoinFeatureOperation, True, False, False, True)]
    point = adsk.core.Point3D.create
    value = adsk.core.ValueInput.createByString
    for case, operation, keep, multiple, swap, component in cases:
        doc = None
        try:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent

            def box(x0, x1, name):
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(x0, 0, 0), point(x1, 2, 0))
                extrude = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value('20 mm'), op.NewBodyFeatureOperation)
                body = extrude.bodies.item(0)
                body.name = name
                return body

            target = box(0, 8 if multiple else 4, 'TargetA')
            tool = box(1 if multiple else 2, 3 if multiple else 6, 'ToolA')
            if swap:
                target, tool = tool, target
            tools = adsk.core.ObjectCollection.create()
            tools.add(tool)
            if multiple:
                tools.add(box(5, 7, 'ToolB'))
            inputs = root.features.combineFeatures.createInput(target, tools)
            inputs.operation = operation
            inputs.isKeepToolBodies = keep
            inputs.isNewComponent = component
            feature = root.features.combineFeatures.add(inputs)
            if feature is None:
                raise RuntimeError('Combine add returned null')
            feature.name = 'ProbeCombine'
            sample = {'file': case+'.f3d', 'requested_new_component': component,
                      'is_new_component': feature.isNewComponent,
                      'output_body_names': [feature.bodies.item(i).name for i in range(feature.bodies.count)],
                      'health_state': feature.healthState, 'warning': feature.errorOrWarningMessage}
            feature.timelineObject.rollTo(True)
            sample.update(operation=feature.operation, keep_tool_bodies=feature.isKeepToolBodies,
                          target_name=feature.targetBody.name,
                          tool_names=[feature.toolBodies.item(i).name for i in range(feature.toolBodies.count)])
            design.timeline.moveToEnd()
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('Combine export failed')
            truth['samples'].append(sample)
        except Exception:
            truth['errors'].append({'case': case, 'error': traceback.format_exc()})
        finally:
            if doc is not None:
                doc.close(False)
            (output/'ground_truth.json').write_text(json.dumps(truth, indent=2))
    (output/'complete.txt').write_text('Combine capture finished; inspect errors.\n')
