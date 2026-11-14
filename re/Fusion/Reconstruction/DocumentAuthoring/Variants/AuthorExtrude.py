import argparse
import hashlib
import json
import lzma
import math
import runpy
import sys
import uuid
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
CIRCLE = runpy.run_path(str(BASE / 'AuthorCircle.py'))
POLICIES = runpy.run_path(str(BASE / 'ExtrudeDefaults.py'))
RECIPE = runpy.run_path(str(BASE / 'RecipeFields.py'))


class ExtrudeAuthor(CIRCLE['CircleAuthor']):
    def __init__(self, specification):
        super().__init__(specification)
        self.defaults.update(POLICIES['policies']())
        self.body_id = str(uuid.uuid4())
        self.brep_part = 'BREP.' + str(uuid.uuid4()) + '.smbh'

    def add_extrude(self):
        self.allocate('dc_extrude', 'DcExtrudeFeature', parent='nodes', named=[])
        self.allocate('profile_model', 'ModelDataRef', parent='nodes')
        self.allocate('profile_region', 'SketchRegionRef', parent='nodes')
        self.allocate('region_recipe', 'SketchRegionRecipe')
        self.allocate('along_parameter', 'Parameter', parent='parameters')
        self.allocate('along_binding', 'DcDoubleParameter', parent='nodes', subjects=['dc_extrude'])
        self.allocate('taper_parameter', 'Parameter', parent='parameters')
        self.allocate('taper_binding', 'DcDoubleParameter', parent='nodes', subjects=['dc_extrude'])
        self.allocate('extrude_tool', 'DcExtrudeToolBody', parent='nodes')
        self.allocate('extrude_progenitors', 'ProgenitorTable')
        self.allocate('curve_progenitor', 'SketchCurveProgenitor', named=[])
        self.allocate('curve_recipe', 'SketchCurveRecipe')
        self.allocate('body_progenitor', 'BodyProgenitor')
        self.allocate('body', 'Body', parent='bodies')
        self.allocate('bodies_root', 'BodiesRoot', root='BodiesRoot')
        self.allocate('body_passive_ids', 'PassiveIdGenerator')
        self.allocate('dc_body', 'DcBody', parent='fragment')
        for role in ('dc_extrude', 'profile_model', 'profile_region', 'extrude_tool'):
            self.allocate(role + '_dynamic', 'DynamicUpdateData')
            self.allocate(role + '_status', 'DcStatus', named=[])
        for role in ('along_binding', 'taper_binding'):
            self.allocate(role + '_dynamic', 'DynamicUpdateData')

    def bind_parameters(self):
        ref = self.reference
        empty = CIRCLE['EMPTY']['DEFAULTS']
        along = empty['numeric']('d2', self.specification['millimeters'], '', self.specification['parameterBirthday'])
        along.update(creationIndex=2, dcParameter=ref('along_binding'), expression=self.specification['parameterName'], isUserDefined=False, name='AlongDistance')
        taper = empty['numeric']('d3', 0.0, '', self.specification['parameterBirthday'])
        taper.update(creationIndex=3, dcParameter=ref('taper_binding'), expression='0 deg', isUserDefined=False, name='TaperAngle', unit='deg')
        self.change('along_parameter', **along)
        self.change('taper_parameter', **taper)
        for role, parameter, runtime_id, value in [('along_binding', 'along_parameter', 1, along['value']), ('taper_binding', 'taper_parameter', 2, 0.0)]:
            self.change(role, value=value, parameter=ref(parameter), rparamId=runtime_id, rrOwnerFeature=ref('dc_extrude'), rParentFeature=ref('dc_extrude'), rDynamicUpdateData=ref(role + '_dynamic'))
            self.change(role + '_dynamic', rOwnerNode=ref(role), timeStamp=self.specification['timeStamp'])
        self.change('parameters', highWaterMark=3)
        self.change('parameter_names', parameterMap=[{'key': self.specification['parameterName'], 'value': ref('length_parameter')}, {'key': 'd2', 'value': ref('along_parameter')}, {'key': 'd3', 'value': ref('taper_parameter')}])
        next(item for item in self.entities if item['role'] == 'parameter_names')['subjects'].extend(['along_parameter', 'taper_parameter'])

    def connect_profile(self):
        ref = self.reference
        self.change('profile_model', dataRefs=[ref('profile_region')], trackingType=65, rParentFeature=ref('dc_extrude'))
        scope = [self.group('PassiveScopeValue', dict(assetId=self.specification['assetId'], scopeEntityIdentifier=str(self.roles['circle_sketch']), scopeIdType=1, segmentId=self.specification['designSegmentId']))]
        self.change('profile_region', rRecipe=ref('region_recipe'), rScope=scope, trackingType=65, rParentFeature=ref('dc_extrude'))
        tag_id = self.specification['firstSketchTag'] + 2
        data = [self.group('SkRegionRecipeDataValue', dict(faceRecipe=[RECIPE['circle_loop'](tag_id)], originalFaceRecipes=[]))]
        self.change('region_recipe', rSketchRegionRef=ref('profile_region'), skRegionRecipe=[data])
        self.change('curve_progenitor', rRecipe=ref('curve_recipe'))
        self.change('curve_recipe', profileEdgeTagData=RECIPE['curve_recipe'](tag_id, True))

    def connect_extrude(self):
        ref = self.reference
        self.change('dc_extrude', rAlongDistance=ref('along_binding'), rTaperAngle=ref('taper_binding'), rExtrudeToolBody=ref('extrude_tool'), profileDataRefs=[ref('profile_model')], dcBodies=[ref('dc_body')], childNodes=[ref(role) for role in ('profile_model', 'profile_region', 'along_binding', 'taper_binding', 'extrude_tool')], featureBaseName='Extrude', featureUserName=self.specification['extrusionName'], rProgenitorTable=ref('extrude_progenitors'), startModelHS=self.specification['historyInitialId'], endModelHS=self.specification['historyCurrentId'])
        self.change('extrude_tool', rExtrudeFeature=ref('dc_extrude'), rParentFeature=ref('dc_extrude'))
        for role in ('dc_extrude', 'profile_model', 'profile_region', 'extrude_tool'):
            self.change(role, status=ref(role + '_status'), rDynamicUpdateData=ref(role + '_dynamic'))
            self.change(role + '_dynamic', rOwnerNode=ref(role), timeStamp=self.specification['timeStamp'])
        self.change('fragment', dcBodies=[ref('dc_body')], featureIndexMap=[{'key': 'DcExtrudeFeatureMetaType', 'value': 1}, {'key': 'DcSketchMetaType', 'value': 1}], nextParamId=2)
        self.change('creation_order', representationFeatures=[ref('dc_sketch'), ref('dc_extrude')])
        operation = self.specification['firstOperationId']
        self.change('feature_ids', enetityIdMap=[{'key': self.roles['dc_sketch'], 'value': [operation]}, {'key': self.roles['dc_extrude'], 'value': [operation + 1, operation + 2]}], featureIdMap=[{'key': operation, 'value': self.roles['dc_sketch']}, {'key': operation + 1, 'value': self.roles['dc_extrude']}, {'key': operation + 2, 'value': self.roles['dc_extrude']}])
        self.change('component', operationSeedId=operation + 3)
        self.change('circle_sketch', isVisible=False)
        self.change('dc_sketch', isVisibleBeforeRollback=False)

    def mass_cache(self):
        point = CIRCLE['EMPTY']['DEFAULTS']['point']
        radius, height = self.specification['radiusMillimeters'] / 10.0, self.specification['millimeters'] / 10.0
        volume = math.pi * radius * radius * height
        transverse = volume * (radius * radius / 4.0 + height * height / 3.0)
        fields = dict(area=2.0 * math.pi * radius * (radius + height), areaPrec=0.0, cog=point(0.0, 0.0, height / 2.0), inertiaPrec=0.0, moi=point(transverse, transverse, volume * radius * radius / 2.0), moiOffDiag=point(), revisionGuid='00000000-0000-0000-0000-000000000000', volume=volume, volumePrec=0.0)
        return [self.group('MassPropertyCacheValue', fields)]

    def connect_body(self):
        ref = self.reference
        self.change('body', actIdentifier=str(self.specification['designSegmentId']) + '_' + str(self.roles['body']), cache=self.mass_cache(), massProperties=self.value('MassPropertiesValue'), persistentId=self.body_id, physicalMaterial=self.value('PhysicalMaterialValue'), rGroupParent=ref('bodies'), userName=self.specification['bodyName'], visualMaterial=self.value('VisualMaterialValue'))
        self.change('bodies_root', rootId='BodiesRoot', rooted=[ref('body')])
        self.change('bodies', creationIndex=1, groupChildren=[ref('body')], passiveIdGenerator=ref('body_passive_ids'))
        self.change('body_passive_ids', rBodies=ref('bodies'))
        self.change('brep_history', mapBodyId=[{'key': self.specification['bodyKey'], 'value': self.roles['body']}], partName=self.brep_part)
        self.change('dc_body', bodyUuid=self.body_id, rBody=ref('body'), rOwnFeature=ref('dc_extrude'))
        label = self.specification['sideFaceLabel'].encode('ascii')
        info = [self.group('FeatureTagInfoValue', dict(facePrimIdData=list(label), facePrimIdOffsets=[0, len(label)], operationId=self.specification['firstOperationId'] + 1, primary=False))]
        self.change('body_progenitor', bodyUuid=self.body_id, featureTagOccMap=[{'key': info, 'value': self.specification['bodyOccurrenceCount']}])
        curve_tag, body_tag = self.specification['curveProgenitorTag'], self.specification['bodyProgenitorTag']
        self.change('extrude_progenitors', ProgenitorTagVec=[{'first': ref('curve_progenitor'), 'second': curve_tag}, {'first': ref('body_progenitor'), 'second': body_tag}], tagId=max(curve_tag, body_tag) + 1)

    def records(self):
        records = super().records()
        for record in records:
            if record['role'] == 'taper_binding' and record['primary']:
                record['value']['frame']['subjects'][0]['indexInObserverVec'] = 1
        return records

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
        self.add_extrude()
        self.bind_parameters()
        self.connect_profile()
        self.connect_extrude()
        self.connect_body()
        return self.records()


def build_extrude(specification):
    author = ExtrudeAuthor(specification)
    records = author.build()
    metadata, bulk, classes = CIRCLE['EMPTY']['serialize'](author, records)
    contract = dict(partName=author.brep_part, bodyEntityId=author.roles['body'], bodyUuid=author.body_id, radiusMillimeters=specification['radiusMillimeters'], heightMillimeters=specification['millimeters'], bodyKey=specification['bodyKey'], operationId=specification['firstOperationId'] + 1, generationRef=specification['generationRef'], currentHistoryId=specification['historyCurrentId'], initialHistoryId=specification['historyInitialId'], historyCurrentStateId=specification['historyCurrentStateId'], nextEntityTag=specification['historyNextEntityTag'], boardStatus=specification['historyBoardStatus'], sideFaceLabel=specification['sideFaceLabel'], topFaceLabel=specification['topFaceLabel'], bottomFaceLabel=specification['bottomFaceLabel'], topEdgeLabel=specification['topEdgeLabel'], bottomEdgeLabel='-' + str(specification['firstSketchTag'] + 2), sketchPrimary=specification['firstSketchTag'] + 2)
    model = {'specification': specification, 'roles': author.roles, 'classes': classes, 'records': records, 'nextId': author.next_id, 'persistentComponentId': author.component_id, 'persistentInstanceId': author.instance_id, 'revisionGuid': author.revision, 'brepContract': contract}
    return {'metadata': metadata, 'bulk': bulk, 'model': model}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--specification', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    arguments = parser.parse_args()
    result = build_extrude(json.loads(arguments.specification.read_text()))
    arguments.output.mkdir(parents=True, exist_ok=True)
    for key, filename in [('metadata', 'MetaStream.dat'), ('bulk', 'BulkStream.dat')]:
        (arguments.output / filename).write_bytes(result[key])
    raw = (json.dumps(result['model'], indent=2) + '\n').encode()
    (arguments.output / 'AuthoredModel.json').write_bytes(raw)
    (arguments.output / 'AuthoredModel.json.xz').write_bytes(lzma.compress(raw, preset=9))
    report = {'schema': 'FusionAuthoredExtrusion/1', 'status': 'authored_native_acceptance_pending', 'entityCount': len(result['model']['roles']), 'recordCount': len(result['model']['records']), 'classCount': len(result['model']['classes']), 'roles': result['model']['roles'], 'bulkSha256': hashlib.sha256(result['bulk']).hexdigest(), 'metadataSha256': hashlib.sha256(result['metadata']).hexdigest(), 'modelSha256': hashlib.sha256(raw).hexdigest(), 'sourceArchive': None, 'runtimeGraphTemplate': None, 'brepContract': result['model']['brepContract']}
    (arguments.output / 'Generation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'roles'}))


if __name__ == '__main__':
    main()
