import argparse
import hashlib
import json
import lzma
import math
import runpy
import sys
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
EMPTY = runpy.run_path(str(BASE.parent / 'AuthorDesign.py'))
POLICIES = runpy.run_path(str(BASE / 'CircleDefaults.py'))


class CircleAuthor(EMPTY['Author']):
    def __init__(self, specification):
        super().__init__(specification)
        self.defaults.update(POLICIES['policies']())

    def attributes(self, **fields):
        return [{'name': name, 'metatype': 'IntrinsicMetaTypeuint64', 'value': value} for name, value in fields.items()]

    def add_circle(self):
        generation = self.specification['sketchGeneration']
        first_tag = self.specification['firstSketchTag']
        self.allocate('circle_sketch', 'MSketch', parent='sketches', named=self.attributes(EntityGenesis=generation))
        self.allocate('sketches_root', 'SketchesRoot', root='SketchesRoot')
        self.allocate('sketch_coordinates', 'CoordinateSystem', parent='component')
        self.allocate('sketch_origin', 'Point3D', parent='circle_sketch', fields={'isFixed': True, 'isFullyConstrained': True, 'isOrigin': True, 'isVisible': False}, named=self.attributes(EntityGenesis=generation, pt_tag=first_tag))
        self.allocate('origin_uses', 'CurveUses', parent='sketch_origin')
        self.allocate('circle_center', 'Point3D', parent='circle_sketch', named=self.attributes(EntityGenesis=generation, pt_tag=first_tag + 1))
        self.allocate('center_uses', 'CurveUses', parent='circle_center')
        self.allocate('circle', 'CircArc3D', parent='circle_sketch', named=self.attributes(EntityGenesis=generation, crv_primary_id=first_tag + 2, crv_secondary_id=0))
        self.allocate('dc_sketch', 'DcSketch', parent='nodes')
        self.allocate('sketch_progenitors', 'ProgenitorTable')
        self.allocate('sketch_plane', 'EntityDataRef', parent='nodes')
        self.allocate('plane_recipe', 'EntityRecipe')
        self.allocate('sketch_matrix', 'DRMatrix', parent='nodes')
        self.allocate('plane_cache', 'ETCachedPlane')
        self.allocate('matrix_cache', 'ETCachedMatrix3d')
        self.allocate('plane_progenitor', 'EntityProgenitor')
        self.allocate('plane_progenitor_recipe', 'EntityRecipe')
        for role in ('dc_sketch', 'sketch_plane', 'sketch_matrix'):
            self.allocate(role + '_dynamic', 'DynamicUpdateData')
            self.allocate(role + '_status', 'DcStatus', named=[])

    def connect_circle(self):
        ref = self.reference
        self.change('circle_sketch', actIdentifier=str(self.specification['designSegmentId']) + '_' + str(self.roles['circle_sketch']), rDcNode=ref('dc_sketch'), UCS=ref('sketch_coordinates'), rSketchGroupParent=ref('sketches'), userName=self.specification['sketchName'])
        self.change('sketches_root', rootId='SketchesRoot', rooted=[ref('circle_sketch')])
        self.change('sketch_origin', curveUses=ref('origin_uses'))
        self.change('circle_center', curveUses=ref('center_uses'))
        self.change('center_uses', geometries=[ref('circle')])
        point = EMPTY['DEFAULTS']['point']
        arc = dict(center=point(), normal=point(0.0, 0.0, 1.0), refVec=point(1.0), radius=self.specification['radiusMillimeters'] / 10.0, startAngle=0.0, endAngle=2.0 * math.pi)
        self.change('circle', arcCurve=arc, rCenterPoint=ref('circle_center'))
        self.change('dc_sketch', rSketch=ref('circle_sketch'), rSketchPlaneMatrix=ref('sketch_matrix'), childNodes=[ref('sketch_plane'), ref('sketch_matrix')], featureBaseName='Sketch', rProgenitorTable=ref('sketch_progenitors'))
        scope = [self.group('PassiveScopeValue', dict(assetId=self.specification['assetId'], scopeEntityIdentifier=self.component_id, scopeIdType=2, segmentId=self.specification['designSegmentId']))]
        self.change('sketch_plane', rRecipe=ref('plane_recipe'), rScope=scope, caches=[ref('plane_cache')], trackingType=33, updateFlag=4, rParentFeature=ref('dc_sketch'))
        self.change('plane_recipe', m_entityId=self.roles['xy_plane'])
        self.change('sketch_matrix', dataRefs=[ref('sketch_plane')], caches=[ref('matrix_cache')], trackingType=4, rParentFeature=ref('dc_sketch'))
        plane = dict(normalReversed=False, origin=point(), uAxis=point(1.0), vAxis=point(0.0, 1.0))
        self.change('plane_cache', rCachedGeometry=plane, progenitor=ref('plane_progenitor'))
        self.change('plane_progenitor', m_entityRecipe=ref('plane_progenitor_recipe'))
        self.change('plane_progenitor_recipe', m_entityId=self.roles['xy_plane'])
        for role in ('dc_sketch', 'sketch_plane', 'sketch_matrix'):
            self.change(role, status=ref(role + '_status'), rDynamicUpdateData=ref(role + '_dynamic'))
            self.change(role + '_dynamic', rOwnerNode=ref(role), timeStamp=self.specification['timeStamp'])
        self.change('sketches', highWaterMark=1, groupChildren=[ref('circle_sketch')])
        next(item for item in self.entities if item['role'] == 'sketches')['named'] = self.attributes(crv_tag_id_idx=self.specification['firstSketchTag'] + 3)
        self.change('fragment', featureIndexMap=[{'key': 'DcSketchMetaType', 'value': 1}])
        self.change('creation_order', representationFeatures=[ref('dc_sketch')])
        self.change('feature_ids', featureIdMap=[{'key': self.specification['firstOperationId'], 'value': self.roles['dc_sketch']}])
        self.change('component', operationSeedId=self.specification['firstOperationId'] + 1)

    def records(self):
        result = []
        for record in super().records():
            if record['role'] == 'circle_sketch' and record['primary']:
                result.append(record | {'value': {'frame': record['value']['frame'], 'groups': record['value']['groups'][:1]}})
                result.append(record | {'primary': False, 'value': {'frame': {'rootId': ''}, 'groups': record['value']['groups'][1:]}})
            else:
                result.append(record)
        return result

    def build(self):
        self.roots()
        self.collections()
        self.compute()
        self.geometry()
        self.units()
        self.component()
        self.connect()
        self.add_circle()
        self.connect_circle()
        return self.records()


def build_circle(specification):
    author = CircleAuthor(specification)
    records = author.build()
    metadata, bulk, classes = EMPTY['serialize'](author, records)
    model = {'specification': specification, 'roles': author.roles, 'classes': classes, 'records': records, 'nextId': author.next_id, 'persistentComponentId': author.component_id, 'persistentInstanceId': author.instance_id, 'revisionGuid': author.revision}
    return {'metadata': metadata, 'bulk': bulk, 'model': model}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--specification', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    arguments = parser.parse_args()
    result = build_circle(json.loads(arguments.specification.read_text()))
    arguments.output.mkdir(parents=True, exist_ok=True)
    for key, filename in [('metadata', 'MetaStream.dat'), ('bulk', 'BulkStream.dat')]:
        (arguments.output / filename).write_bytes(result[key])
    raw = (json.dumps(result['model'], indent=2) + '\n').encode()
    (arguments.output / 'AuthoredModel.json').write_bytes(raw)
    (arguments.output / 'AuthoredModel.json.xz').write_bytes(lzma.compress(raw, preset=9))
    report = {'schema': 'FusionAuthoredCircle/1', 'status': 'authored_native_acceptance_pending', 'entityCount': len(result['model']['roles']), 'recordCount': len(result['model']['records']), 'classCount': len(result['model']['classes']), 'roles': result['model']['roles'], 'bulkSha256': hashlib.sha256(result['bulk']).hexdigest(), 'metadataSha256': hashlib.sha256(result['metadata']).hexdigest(), 'modelSha256': hashlib.sha256(raw).hexdigest(), 'sourceArchive': None, 'runtimeGraphTemplate': None}
    (arguments.output / 'Generation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'roles'}))


if __name__ == '__main__':
    main()
