"""Read Circular Pattern getters from two owned saved archive imports.

Imports each study archive to a new document, reads retained/fresh/reversed
handles, and closes only that imported document without saving. Never exports,
modifies, closes or activates a pre-existing user document. Tokens are opaque.
"""
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

FILES = ('circularmodes-45f859c1f1b6/body_full.f3d',
         'circularmodes-45f859c1f1b6/body_negative.f3d')


def run(context):
    app = adsk.core.Application.get()
    root = Path(__file__).resolve().parent
    output = root/('circulargetterhandles-'+uuid.uuid4().hex[:12])
    output.mkdir()
    report = {'fusion_version': app.version, 'source': 'Actual API getters after importing owned saved archives',
              'samples': [], 'errors': [], 'status': 'running',
              'scope': 'Import readback only; no model edits, exports, native ID assignments or transform correction'}

    def save():
        (output/'ground_truth.json').write_text(json.dumps(report, indent=2)+'\n')

    def safe(callback):
        try:
            return {'value': callback()}
        except Exception:
            return {'error': traceback.format_exc()}

    def matrix(element):
        return [float(x) for x in element.transform.asArray()]

    def face_rows(element):
        rows = []
        for face in element.faces:
            body = face.body
            rows.append({'face_token': face.entityToken, 'body_token': body.entityToken,
                         'body_name': body.name,
                         'body_bounds_cm': {'min': list(body.boundingBox.minPoint.asArray()),
                                            'max': list(body.boundingBox.maxPoint.asArray())}})
        return rows

    def retained(element, index):
        return {'requested_collection_index': index, 'id_before': safe(lambda: element.id),
                'name': safe(lambda: element.name),
                'parent_feature_name': safe(lambda: element.parentFeature.name),
                'transform_first': safe(lambda: matrix(element)),
                'transform_second': safe(lambda: matrix(element)),
                'is_suppressed': safe(lambda: element.isSuppressed),
                'faces': safe(lambda: face_rows(element)), 'id_after': safe(lambda: element.id)}

    save()
    for filename in FILES:
        document = None
        sample = {'file': filename, 'archive_sha256': hashlib.sha256((root/filename).read_bytes()).hexdigest(),
                  'status': 'importing'}
        report['samples'].append(sample)
        save()
        try:
            options = app.importManager.createFusionArchiveImportOptions(str(root/filename))
            document = app.importManager.importToNewDocument(options)
            if document is None:
                raise RuntimeError('Archive import did not return an owned new document')
            sample['status'] = 'reading'
            save()
            design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
            patterns = design.rootComponent.features.circularPatternFeatures
            if patterns.count != 1:
                raise RuntimeError('Expected one Circular Pattern in the owned fixture')
            feature = patterns.item(0)
            collection = feature.patternElements
            handles = [collection.item(i) for i in range(collection.count)]
            sample['settings'] = {'quantity': feature.quantity.value, 'total_angle_radians': feature.totalAngle.value,
                                  'is_symmetric': feature.isSymmetric,
                                  'pattern_entity_type': feature.patternEntityType,
                                  'suppressed_ids': list(feature.suppressedElementsIds),
                                  'result_body_count': design.rootComponent.bRepBodies.count}
            sample['retained_forward'] = [retained(e, i) for i, e in enumerate(handles)]
            sample['fresh_per_property'] = [
                {'requested_collection_index': i, 'id': safe(lambda i=i: feature.patternElements.item(i).id),
                 'is_suppressed': safe(lambda i=i: feature.patternElements.item(i).isSuppressed),
                 'transform': safe(lambda i=i: matrix(feature.patternElements.item(i)))}
                for i in range(collection.count)]
            sample['repeated_item'] = [
                {'requested_collection_index': i, 'first': retained(collection.item(i), i),
                 'second': retained(collection.item(i), i)} for i in range(collection.count)]
            sample['retained_reverse'] = [retained(handles[i], i) for i in reversed(range(len(handles)))]
            sample['python_handles_are_pairwise_distinct'] = all(a is not b for i, a in enumerate(handles) for b in handles[i+1:])
            sample['status'] = 'read_complete'
        except Exception:
            sample['status'] = 'error'
            report['errors'].append({'file': filename, 'error': traceback.format_exc()})
        finally:
            if document is not None:
                sample['close_owned_document'] = safe(lambda: document.close(False))
            save()
    report['status'] = 'complete'
    save()
    (output/'complete.txt').write_text('Actual imported-archive getter probe finished; consult errors.\n')
