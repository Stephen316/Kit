"""Capture local study-owned Emboss/deboss profiles and numeric controls."""
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/('embossmodes-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': []}
    point = adsk.core.Point3D.create
    value = adsk.core.ValueInput.createByString
    for case in ['raised', 'engraved', 'shifted', 'rotated', 'no_chain', 'multiple_profiles']:
        doc = None
        try:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            seed_sketch = root.sketches.add(root.xYConstructionPlane)
            seed_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(6, 4, 0))
            seed = root.features.extrudeFeatures.addSimple(seed_sketch.profiles.item(0), value('20 mm'),
                        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.bodies.item(0).name = 'TargetPart'
            top = seed.endFaces.item(0)
            plane_input = root.constructionPlanes.createInput()
            plane_input.setByOffset(root.xYConstructionPlane, value('25 mm'))
            plane = root.constructionPlanes.add(plane_input)
            sketch = root.sketches.add(plane)
            sketch.name = 'EmbossProfiles'
            sketch.sketchCurves.sketchCircles.addByCenterRadius(point(2, 2, 0), .4)
            if case == 'multiple_profiles':
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(4, 2, 0), .3)
            inputs = root.features.embossFeatures.createInput([sketch.profiles.item(i) for i in range(sketch.profiles.count)],
                        [top], value('-1.5 mm' if case == 'engraved' else '2 mm'))
            inputs.isTangentChain = case != 'no_chain'
            if case == 'shifted':
                inputs.horizontalDistance = value('3 mm')
                inputs.verticalDistance = value('-2 mm')
            if case == 'rotated':
                inputs.rotationAngle = value('17 deg')
            feature = root.features.embossFeatures.add(inputs)
            if feature is None:
                raise RuntimeError('Emboss add returned null')
            feature.name = 'ProbeEmboss'
            sample = {'file': case+'.f3d', 'health_state': feature.healthState,
                      'warning': feature.errorOrWarningMessage,
                      'output_body_names': [b.name for b in feature.bodies]}
            feature.timelineObject.rollTo(True)
            sample['settings'] = {'depth_cm': feature.depth.value,
                     'horizontal_distance_cm': feature.horizontalDistance.value,
                     'vertical_distance_cm': feature.verticalDistance.value,
                     'rotation_angle_radians': feature.rotationAngle.value,
                     'is_tangent_chain': feature.isTangentChain,
                     'profiles': [{'kind': p.objectType, 'sketch_name': p.parentSketch.name,
                                   'loop_count': p.profileLoops.count} for p in feature.profiles],
                     'input_faces': [{'body_name': f.body.name, 'geometry_type': f.geometry.objectType,
                                      'point_on_face_cm': f.pointOnFace.asArray(), 'area_cm2': f.area} for f in feature.inputFaces]}
            design.timeline.moveToEnd()
            sample['parameters'] = [{'name': p.name, 'role': p.role, 'value': p.value, 'unit': p.unit,
                                    'created_by': getattr(p.createdBy, 'name', None)} for p in root.modelParameters]
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('Emboss export failed')
            truth['samples'].append(sample)
        except Exception:
            truth['errors'].append({'case': case, 'error': traceback.format_exc()})
        finally:
            if doc is not None:
                doc.close(False)
            (output/'ground_truth.json').write_text(json.dumps(truth, indent=2))
    (output/'complete.txt').write_text('Emboss capture finished; inspect errors.\n')
