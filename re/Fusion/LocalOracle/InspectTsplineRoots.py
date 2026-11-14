import hashlib
import json
import lzma
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parents[3]
folder = Path(__file__).resolve().parent / 'TSplineCodec' / 'RootVariants'
preparation_path = folder / 'Preparation.json'
preparation = json.loads(preparation_path.read_bytes())
reference_path = folder.parent / 'Evaluation' / 'Capture.json'
reference = next(item for item in json.loads(reference_path.read_bytes())['cases']
                 if item['name'] == 'NativePrimitive')
cage_reference_path = folder.parent / 'NativeAcceptance.json'
cage_case = next(item for item in json.loads(cage_reference_path.read_bytes())['cases']
                 if item['name'] == 'AuthoredClosedCage')
cage_reference = next(item for item in cage_case['variants']
                      if item['variant'] == 'NativePrimitive')
app = adsk.core.Application.get()
original = app.activeDocument
document = None
form = None
editing = False
report = {
    'fusion_version': app.version,
    'scope': 'Native import of seven independently authored root/allocation variants; initial and edited cage plus default and very-high physical properties',
    'preparation_sha256': hashlib.sha256(preparation_path.read_bytes()).hexdigest(),
    'reference_file': str(reference_path.relative_to(root)),
    'reference_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest(),
    'cage_reference_file': str(cage_reference_path.relative_to(root)),
    'cage_reference_sha256': hashlib.sha256(cage_reference_path.read_bytes()).hexdigest(),
    'comparison_tolerances': {'relative': 1e-8, 'absolute': 1e-8},
    'cases': [],
}
observations = {}


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def checkpoint():
    data = lzma.compress(json.dumps(observations, separators=(',', ':'), allow_nan=False).encode())
    (folder / 'Observations.json.xz').write_bytes(data)
    report['observation_sha256'] = hashlib.sha256(data).hexdigest()
    (folder / 'Capture.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')


def point(value):
    return list(value.asArray())


def key(value):
    return tuple(round(item, 12) for item in value.asArray())


def cage(body, label):
    observations[label] = {
        'control_points_cm': [point(item.geometry) for item in body.vertices],
        'smooth_points_cm': [point(item.smoothGeometry) for item in body.vertices],
        'edges': [{'start': point(item.startVertex.geometry), 'end': point(item.endVertex.geometry),
                   'creased': item.isCreased} for item in body.edges],
        'faces': [[point(item.geometry) for item in face.vertices] for face in body.faces],
    }
    return {
        'faces': body.faces.count, 'edges': body.edges.count, 'vertices': body.vertices.count,
        'control_sha256': digest(sorted(key(item.geometry) for item in body.vertices)),
        'smooth_sha256': digest(sorted(key(item.smoothGeometry) for item in body.vertices)),
        'edge_crease_sha256': digest(sorted((tuple(sorted((key(item.startVertex.geometry), key(item.endVertex.geometry)))),
                                             item.isCreased) for item in body.edges)),
        'face_incidence_sha256': digest(sorted(tuple(sorted(key(item.geometry) for item in face.vertices))
                                               for face in body.faces)),
    }


def properties(body):
    result = {
        'faces': body.faces.count, 'edges': body.edges.count, 'vertices': body.vertices.count,
        'solid': body.isSolid, 'bounds_cm': [point(body.boundingBox.minPoint), point(body.boundingBox.maxPoint)],
        'default_area_cm2': body.area, 'default_volume_cm3': body.volume,
    }
    for name, accuracy in [('low', adsk.fusion.CalculationAccuracy.LowCalculationAccuracy),
                           ('very_high', adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)]:
        value = body.getPhysicalProperties(accuracy)
        result[name] = {'accuracy': value.accuracy, 'area_cm2': value.area,
                        'volume_cm3': value.volume, 'center_cm': point(value.centerOfMass)}
    return result


def differences(expected, actual, path='state'):
    if isinstance(expected, dict) and isinstance(actual, dict):
        if expected.keys() != actual.keys():
            return [{'path': path, 'expected_keys': sorted(expected), 'actual_keys': sorted(actual)}]
        return [difference for name in expected
                for difference in differences(expected[name], actual[name], path + '.' + name)]
    if isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        if len(expected) != len(actual):
            return [{'path': path, 'expected_count': len(expected), 'actual_count': len(actual)}]
        return [difference for index, (left, right) in enumerate(zip(expected, actual))
                for difference in differences(left, right, path + '.' + str(index))]
    if isinstance(expected, float) and isinstance(actual, (int, float)):
        if isclose(expected, actual, rel_tol=1e-8, abs_tol=1e-8):
            return []
        return [{'path': path, 'expected': expected, 'actual': actual,
                 'delta': actual - expected, 'relative_delta': (actual - expected) / expected if expected else None}]
    return [] if expected == actual else [{'path': path, 'expected': expected, 'actual': actual}]


try:
    for prepared in preparation['cases']:
        case = {'name': prepared['name'], 'stages': {}}
        report['cases'].append(case)
        try:
            source = root / prepared['output_file']
            if hashlib.sha256(source.read_bytes()).hexdigest() != prepared['output_sha256']:
                raise RuntimeError('Prepared root variant changed')
            case['source_sha256'] = prepared['output_sha256']
            document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
            form = design.rootComponent.features.formFeatures.add()
            form.name = 'Qualified Form'
            if not form.startEdit():
                raise RuntimeError('Form edit did not start')
            editing = True
            body = form.tSplineBodies.addByTSMFile(str(source))
            if body is None:
                raise RuntimeError('Root variant import failed')
            body.name = 'Qualified Cage'
            for stage in ('Initial', 'Edited'):
                if stage == 'Edited':
                    if not form.startEdit():
                        raise RuntimeError('Form edit did not reopen')
                    editing = True
                    body = form.tSplineBodies.item(0)
                    vertex = min(body.vertices, key=lambda item: key(item.geometry))
                    case['edited_control_point_cm'] = point(vertex.geometry)
                    if not vertex.move(adsk.core.Vector3D.create(.11, .07, .13)):
                        raise RuntimeError('Root variant control-point edit failed')
                label = prepared['name'] + stage
                cage_value = cage(body, label)
                path = folder / (label + '.tsm')
                path.write_text(body.getTSMDescription())
                if not form.finishEdit():
                    raise RuntimeError('Form edit did not finish')
                editing = False
                if not design.computeAll() or form.healthState != 0 or design.rootComponent.bRepBodies.count != 1:
                    raise RuntimeError('Root variant did not solve as one healthy body')
                solved = properties(design.rootComponent.bRepBodies.item(0))
                stage_value = {'tsm_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                               'cage': cage_value, 'properties': solved,
                               'timeline': [{'health': item.healthState, 'message': item.errorOrWarningMessage}
                                            for item in design.timeline]}
                stage_value['property_differences'] = differences(reference['stages'][stage]['properties'], solved)
                stage_value['cage_differences'] = differences(cage_reference['stages'][stage.lower() + '_cage'], cage_value)
                stage_value['matches_native_primitive'] = not stage_value['property_differences'] and not stage_value['cage_differences']
                case['stages'][stage] = stage_value
                checkpoint()
            case['status'] = 'captured'
            case['matches_native_primitive'] = all(item['matches_native_primitive'] for item in case['stages'].values())
        except Exception:
            case['status'] = 'failed'
            case['traceback'] = traceback.format_exc()
        finally:
            if editing and form is not None:
                form.finishEdit()
            editing = False
            if document is not None:
                document.close(False)
            document = None
            form = None
            checkpoint()
    report['status'] = 'captured' if all(item['status'] == 'captured' for item in report['cases']) else 'partial_failure'
    report['matching_variants'] = [item['name'] for item in report['cases'] if item.get('matches_native_primitive')]
finally:
    if editing and form is not None:
        form.finishEdit()
    if document is not None:
        document.close(False)
    if original is not None and original.isValid:
        original.activate()
    report['documents_after'] = app.documents.count
    checkpoint()
