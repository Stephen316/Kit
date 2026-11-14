import argparse
import copy
import hashlib
import json
import runpy
import struct
import sys
import time
import uuid
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
API = runpy.run_path(str(BASE.parent / 'EntityGraph' / 'DecodeGraph.py'))
DEFAULTS = runpy.run_path(str(BASE / 'AuthorDefaults.py'))


class Author:
    def __init__(self, specification):
        self.specification = specification
        self.codec = API['GraphCodec']({'classes': {}})
        self.names = {item['name'].removesuffix('MetaType'): item for item in self.codec.schema.values()}
        self.defaults = DEFAULTS['defaults']()
        self.roles = {}
        self.entities = []
        self.next_id = specification['firstDesignId']
        self.revision = str(uuid.uuid4())
        self.component_id = str(uuid.uuid4())
        self.instance_id = str(uuid.uuid4())

    def allocate(self, role, name, parent=None, root='', fields=None, named=None, subjects=None):
        if role in self.roles:
            raise ValueError('Duplicate entity role ' + role)
        self.roles[role] = self.next_id
        self.next_id += 1
        self.entities.append(dict(role=role, name=name, parent=parent, root=root, fields=fields or {}, named=named, subjects=subjects or []))

    def reference(self, role):
        return None if role is None else {'entityId': self.roles[role]}

    def act_reference(self, role):
        return {'entityId': self.specification['actRoles'][role], 'segmentId': self.specification['actSegmentId']}

    def group(self, name, fields):
        return {'identifier': self.names[name]['identifier'], 'fields': fields}

    def value(self, name, changes=None):
        entity = self.names[name]
        result = []
        for group in self.codec.groups(entity['identifier']):
            current = self.codec.schema[group['metatype_identifier'].upper()]['name'].removesuffix('MetaType')
            result.append(self.group(current, copy.deepcopy(self.defaults[current]) | (changes or {}).get(current, {})))
        return result

    def change(self, role, **fields):
        entity = next(item for item in self.entities if item['role'] == role)
        entity['fields'].update(fields)

    def localize(self, text):
        return [self.group('GlobalizedStringValue', dict(defaultValue=text, globalized=False, id='', moduleName='', value=text))]

    def roots(self):
        self.allocate('settings', 'CommonDataAssetSettings', root='AssetSettings', fields=DEFAULTS['settings']())
        self.allocate('protein', 'ProteinAssetManager', root='ProteinAssetManager')
        self.allocate('component', 'FusionComponent', parent='root_instance', named=[])
        self.allocate('components_root', 'ComponentsRoot', root='ComponentsRoot')
        self.allocate('root_instance', 'ComponentInstance', root='rootInstance', named=[], subjects=['component'])
        self.allocate('instances_root', 'ComponentInstancesRoot', root='ComponentInstancesRoot')
        self.allocate('thread_settings', 'ThreadSettings')
        self.allocate('units', 'UnitSystems', root='UnitSystems')
        self.allocate('unit_system', 'UnitSystem', parent='units')
        self.allocate('pmi_settings', 'PMISettings')
        self.allocate('named_views', 'NamedViews')
        self.allocate('named_lights', 'NamedLights')
        self.allocate('tracked', 'NamedTrackedEntitySet', root='NamedTrackedEntitySet')
        self.allocate('placeholder', 'WorkingModelPlaceholderRoot', root='WorkingModelPlaceholderRoot')
        self.allocate('post_office', 'ComponentPostOffice', root='ComponentPostOffice')
        self.allocate('scene_serializer', 'OGSSerializer', root='OGSSerializer')

    def collections(self):
        names = {
            'overrides': 'Overrides', 'component_instances': 'ComponentInstances', 'bodies': 'Bodies',
            'sketches': 'Sketches', 'work_geometries': 'WorkGeometries', 'joint_origins': 'JointOrigins',
            'constraints': 'AssyConstraints', 'constraint_occurrences': 'AssyConstraintOccurrences',
            'contacts': 'ContactSets', 'motion_studies': 'MotionStudies', 'parameters': 'ParameterTable',
            'surface_groups': 'SurfaceGroups', 'selection_groups': 'SelectionGroups',
            'work_groups': 'WorkGeometryCustomGroups', 'sketch_groups': 'SketchCustomGroups',
            'cache_bodies': 'Bodies', 'features': 'Features', 'origin': 'OriginWorkGeometry',
            'relationships': 'Relationships', 'subd': 'SubDSurfaceNodes', 'canvases': 'Canvases',
            'feature_groups': 'DcGroupFeatures', 'decals': 'DecalPatches', 'annotations': 'PMIAnnotations',
            'meshes': 'MeshBodies', 'canvas_groups': 'CanvasGroups', 'deformers': 'LatticeRigDeformers',
            'eip_contexts': 'EIPContexts', 'history_free_manager': 'HistoryFreeUpdateManager', 'arrangements': 'Arrangements',
        }
        for role, name in names.items():
            self.allocate(role, name, parent='component')
        self.allocate('brep_history', 'BRepHistorySerializer')
        self.allocate('cache_serializer', 'BRepSerializer')
        self.allocate('passive_ids', 'PassiveIdGenerator')
        self.allocate('parameter_names', 'ParameterSearchByNameHelper', subjects=['parameters', 'length_parameter'])
        self.allocate('local_context', 'EIPContext', parent='eip_contexts')
        self.allocate('length_parameter', self.codec.schema['7A6A3D31-BE74-4E19-9115-20642944C2E4']['name'].removesuffix('MetaType'), parent='parameters', fields=DEFAULTS['numeric'](self.specification['parameterName'], self.specification['millimeters'], self.specification['parameterComment'], self.specification['parameterBirthday']))

    def compute(self):
        self.allocate('fragment', 'DcDesignFragment', parent='component')
        self.allocate('nodes', 'DcNodes', parent='fragment')
        for role, name in [('compute', 'DcComputeManager'), ('dependency', 'DcDependencyManager'), ('association', 'DcAssociationManager'), ('feature_ids', 'DcFeatureIdManager'), ('xref', 'DcXRefManager')]:
            self.allocate(role, name)
        self.allocate('dc_component', 'DcComponent', parent='nodes')
        self.allocate('dynamic', 'DynamicUpdateData')
        self.allocate('creation_order', 'DcCreationOrderFeatures')
        self.allocate('occurrence', 'DcOccurrence')

    def geometry(self):
        point = DEFAULTS['point']
        self.allocate('origin_point', 'WorkPoint', parent='origin', fields={'originName': 'O'})
        axes = [('x_axis', 'X', point(1.0)), ('y_axis', 'Y', point(0.0, 1.0)), ('z_axis', 'Z', point(0.0, 0.0, 1.0))]
        for role, name, direction in axes:
            self.allocate(role, 'WorkAxis', parent='origin', fields={'originName': name, 'line': {'pointOnLine': point(), 'parametricDirection': direction}})
        for role, name, u_axis, v_axis in [('xy_plane', 'XY', point(1.0), point(0.0, 1.0)), ('xz_plane', 'XZ', point(1.0), point(0.0, 0.0, 1.0)), ('yz_plane', 'YZ', point(0.0, 1.0), point(0.0, 0.0, 1.0))]:
            self.allocate(role, 'WorkPlane', parent='origin', fields={'originName': name, 'plane': {'normalReversed': False, 'origin': point(), 'uAxis': u_axis, 'vAxis': v_axis}})

    def units(self):
        choices = [('ModelingLength', 'millimeter'), ('ModelingMass', 'gram')]
        choices += [(number, unit) for number, unit in [(0, 'meter'), (1, 'kilogram'), (2, 'second'), (3, 'celsius'), (4, 'ampere'), (5, 'Mole'), (6, 'candela'), (7, 'degree'), (8, 'dollar'), (10, 'MetersPerSecond'), (12, 'liter'), (13, 'pascal'), (14, 'newton'), (15, 'watt'), (16, 'joule'), (31, 'percent'), (33, 'pieces')]]
        for key, unit in choices:
            fields = {'name': self.localize(unit), 'unitString': unit}
            fields['id' if isinstance(key, str) else 'eSimpleUnitType'] = key
            self.allocate('unit_' + str(key), 'UnitSystemChoiceById' if isinstance(key, str) else 'UnitSystemChoiceByUnit', parent='unit_system', fields=fields)
        self.change('unit_system', id='MmMKS', name=self.localize('Millimeter MKS'))

    def component(self):
        ref = self.reference
        body = dict(isAsBuiltPositions=True, m_opacity=1.0, mappedProperties=[], operationSeedId=300, rClientContainers=[{'key': 'arrangementsContainer', 'value': ref('arrangements')}], rFeatRuleData=None, rLibaryItems=None, rSheetmetalData=None, rXRefManager=None, subType=0)
        links = dict(m_rCanvases='canvases', m_rDecalPatches='decals', m_rDeformers='deformers', m_rFeatures='features', m_rHFUM='history_free_manager', m_rOriginWorkGeometry='origin', m_rRelationships='relationships', m_rVSubDSurfaces='subd', rAnnotations='annotations', rCacheBodies='cache_bodies', rCanvasGroups='canvas_groups', rDesignFragment='fragment', rEIPContexts='eip_contexts', rGroupFeatures='feature_groups', rMeshBodies='meshes', m_SketchCustomGroups='sketch_groups', m_WorkGeometryCustomGroups='work_groups', rAssyConstraintOccs='constraint_occurrences', rAssyConstraints='constraints', rBodies='bodies', rContactSets='contacts', rJointOrigins='joint_origins', rMotionStudies='motion_studies', rParameterTable='parameters', rSelectionGroups='selection_groups', rSketches='sketches', rSurfaceGroups='surface_groups', rWorkGeometries='work_geometries', overrides='overrides', rComponentBaseInstances='component_instances')
        body.update({name: ref(role) for name, role in links.items()})
        body.update(massProperties=self.value('MassPropertiesValue'), rPersistedCustomGraphics=None, createdPreACT=False, creationIndex=0, cyclingColor=DEFAULTS['color'](0.8, 0.8, 0.8), defaultPhysicalMaterial=self.value('PhysicalMaterialValue'), isVisible=True, persistentId=self.component_id, rACTComponent=self.act_reference('component'), rOwningDeriveFeature=None, revisionGuid=self.revision, userName=self.specification['title'])
        self.change('component', **body)
        self.change('root_instance', bGroundToParent=False, bRigidSubAssembly=False, creationIndex=0, initialTransform={'identity': True}, lastSavedTargetRevisionGuid=self.revision, persistentId=self.instance_id, rACTInstance=self.act_reference('root_instance'), rOwningDeriveFeature=None, rTargetComponent=ref('component'), transform={'identity': True}, userName='', xAssetLinkName='')

    def connect(self):
        ref = self.reference
        self.change('components_root', rootId='ComponentsRoot', rooted=[ref('component')])
        self.change('instances_root', rootId='ComponentInstancesRoot', rooted=[ref('root_instance')])
        self.change('component_instances', rACTInstances=self.act_reference('instances'))
        self.change('settings', activeUnitSystem=ref('unit_system'), threadSettings=ref('thread_settings'), pmiSettings=ref('pmi_settings'), namedViews=ref('named_views'), rNamedLights=ref('named_lights'))
        self.change('bodies', rBRepSerializer=ref('brep_history'), surfaceGroups=ref('surface_groups'))
        self.change('brep_history', rBodies=ref('bodies'))
        self.change('cache_bodies', rBRepSerializer=ref('cache_serializer'))
        self.change('cache_serializer', rBodies=ref('cache_bodies'), topEntityPIDGenerator=ref('passive_ids'))
        self.change('sketches', sketchCustomGroups=ref('sketch_groups'))
        next(item for item in self.entities if item['role'] == 'sketches')['named'] = [{'name': 'crv_tag_id_idx', 'metatype': 'IntrinsicMetaTypeuint64', 'value': 100}]
        self.change('work_geometries', workGeometryCustomGroups=ref('work_groups'))
        self.change('canvases', canvasGroups=ref('canvas_groups'))
        self.change('parameters', highWaterMark=1, rParameterSearchByNameHelper=ref('parameter_names'))
        self.change('parameter_names', parameterMap=[{'key': self.specification['parameterName'], 'value': ref('length_parameter')}])
        self.change('fragment', dcBodies=[], featureIndexMap=[], nextParamId=0, occurrences=[ref('occurrence')], rAssociationManager=ref('association'), rComputeManager=ref('compute'), rCreationOrderFeatures=ref('creation_order'), rDependencyManager=ref('dependency'), rFeatureIdManager=ref('feature_ids'), rNodes=ref('nodes'), rXRefIdManager=ref('xref'))
        for role in ('compute', 'dependency', 'association', 'feature_ids', 'xref'):
            self.change(role, rOwnerFragment=ref('fragment'))
        self.change('dc_component', rFusionComponent=ref('component'), rDynamicUpdateData=ref('dynamic'))
        self.change('dynamic', rOwnerNode=ref('dc_component'), timeStamp=self.specification['timeStamp'])
        self.change('creation_order', rFragment=ref('fragment'))
        path = [self.group('OccurrencePathValue', {}), self.group('BaseOccurrencePathValue', dict(componentInstances=[], creationState=3, passiveOccurrencePath=self.value('ACTPassivePathValue'), sourceACTComponent=self.act_reference('component'), sourceComponent=ref('component')))]
        self.change('occurrence', contextPositionMap=[], dcAssyConstraintOccurrences=[], path=path, stateIdx=-1, states=[])

    def records(self):
        result = []
        for entity in self.entities:
            schema = self.names[entity['name']]
            fields = copy.deepcopy(entity['fields'])
            groups = []
            lineage = self.codec.groups(schema['identifier'])
            available = {member['name'] for group in lineage for member in self.codec.members(group)}
            if set(fields) - available:
                raise ValueError('Unknown authored fields ' + entity['role'] + ': ' + str(set(fields) - available))
            for group in lineage:
                name = self.codec.schema[group['metatype_identifier'].upper()]['name'].removesuffix('MetaType')
                values = copy.deepcopy(self.defaults.get(name, {}))
                for member in self.codec.members(group):
                    key = member['name']
                    if key in fields:
                        values[key] = fields[key]
                    elif key == 'rParent':
                        values[key] = self.reference(entity['parent'])
                    elif key == 'children':
                        values[key] = [self.reference(child['role']) for child in self.entities if child['parent'] == entity['role']]
                expected = {member['name'] for member in self.codec.members(group)}
                if set(values) != expected:
                    raise ValueError(entity['role'] + ':' + name + ' missing=' + str(expected - set(values)) + ' extra=' + str(set(values) - expected))
                groups.append(self.group(name, values))
            split = next((index for index, group in enumerate(groups) if index and schema['addin'] == 'Fusion' and self.codec.schema[group['identifier'].upper()]['addin'] != 'Fusion'), len(groups))
            frame = dict(rootId=entity['root'], hasSubjects=bool(entity['subjects']), subjects=[{'subject': self.reference(role), 'indexInObserverVec': 0} for role in entity['subjects']], hasNamedMetadata=entity['named'] is not None, namedMetadata=entity['named'] or [])
            result.append(dict(role=entity['role'], identity=self.roles[entity['role']], primary=True, value={'frame': frame, 'groups': groups[:split]}))
            if split < len(groups):
                result.append(dict(role=entity['role'], identity=self.roles[entity['role']], primary=False, value={'frame': {'rootId': entity['root']}, 'groups': groups[split:]}))
        return result

    def build(self):
        self.roots()
        self.collections()
        self.compute()
        self.geometry()
        self.units()
        self.component()
        self.connect()
        return self.records()


def declarations(author, records):
    selected = set()
    def visit(identity):
        identity = identity.upper()
        if identity in selected:
            return
        selected.add(identity)
        schema = author.codec.schema[identity]
        if schema['base_identifier']:
            visit(schema['base_identifier'])
        if identity == API['ROOT']:
            return
        for member in author.codec.members(author.codec.own_set(identity)):
            metatype = member['metatype']
            if metatype.get('category', {}).get('name') == 'value':
                visit(metatype['identifier'])
    def walk(value):
        if isinstance(value, dict):
            if 'identifier' in value and 'fields' in value:
                visit(value['identifier'])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(records)
    output = {}
    for index, identity in enumerate(sorted(selected)):
        schema = author.codec.schema[identity]
        output[256 + index] = dict(identifier=schema['identifier'], baseIdentifier=schema['base_identifier'] or '', schemaVersion=schema['metatype_current_version'], namespace=schema['addin'])
    return output


def serialize(author, records):
    classes = declarations(author, records)
    codes = {entry['identifier'].upper(): code for code, entry in classes.items()}
    output, indices = bytearray(), {True: [], False: []}
    owners = {code: [] for code in classes}
    text = API['TOOLS']['encode_text']
    for record in records:
        code = codes[record['value']['groups'][0]['identifier'].upper()]
        record['classCode'] = code
        indices[record['primary']].append((record['identity'], len(output)))
        if record['primary']:
            owners[code].append(record['identity'])
        output.extend(text(str(code)) + struct.pack('<Q', record['identity']) + API['emit_record'](author.codec, record['value'], record['primary']))
    specification = author.specification
    kind = 'FusionDesignSegmentType'
    software = (2706 << 50) | (1 << 38) | 17
    metadata = bytearray(text(kind) + struct.pack('<I', specification['designSegmentId']) + text('00000000-0000-0000-0000-000000000000', True))
    metadata.extend(struct.pack('<IIQ', 1234, 8, software) + text(kind) + text('Fusion') + struct.pack('<III', 1, 0, len(classes)))
    for code, entry in classes.items():
        metadata.extend(text(entry['identifier']) + text(entry['baseIdentifier']) + struct.pack('<I', entry['schemaVersion']) + text(entry['namespace']))
        metadata.extend(struct.pack('<I', len(owners[code])) + b''.join(struct.pack('<Q', value) for value in owners[code]))
    roots = [author.roles[entity['role']] for entity in author.entities if entity['root']]
    metadata.extend(struct.pack('<I', len(roots)) + b''.join(struct.pack('<Q', value) for value in roots))
    for primary in (True, False):
        metadata.extend(struct.pack('<I', len(indices[primary])) + b''.join(struct.pack('<QQ', *entry) for entry in indices[primary]))
    extensions = specification['extensionVersions']
    metadata.extend(struct.pack('<QII', author.next_id, 0, len(extensions)))
    for name, version in extensions.items():
        metadata.extend(text(name) + struct.pack('<I', version))
    return bytes(metadata), bytes(output), classes


def build_document(specification):
    author = Author(specification)
    records = author.build()
    metadata, bulk, classes = serialize(author, records)
    model = {'specification': specification, 'roles': author.roles, 'classes': classes, 'records': records, 'nextId': author.next_id, 'persistentComponentId': author.component_id, 'persistentInstanceId': author.instance_id, 'revisionGuid': author.revision}
    return {'metadata': metadata, 'bulk': bulk, 'model': model}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--specification', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    result = build_document(json.loads(arguments.specification.read_text()))
    arguments.output.mkdir(parents=True, exist_ok=True)
    for key, filename in [('metadata', 'MetaStream.dat'), ('bulk', 'BulkStream.dat')]:
        (arguments.output / filename).write_bytes(result[key])
    raw = (json.dumps(result['model'], indent=2) + '\n').encode()
    (arguments.output / 'AuthoredModel.json').write_bytes(raw)
    report = {'schema': 'FusionAuthoredDesign/1', 'status': 'authored_native_acceptance_pending', 'entityCount': len(result['model']['roles']), 'recordCount': len(result['model']['records']), 'classCount': len(result['model']['classes']), 'roles': result['model']['roles'], 'bulkSha256': hashlib.sha256(result['bulk']).hexdigest(), 'metadataSha256': hashlib.sha256(result['metadata']).hexdigest(), 'modelSha256': hashlib.sha256(raw).hexdigest(), 'sourceArchive': None, 'runtimeGraphTemplate': None}
    (arguments.output / 'Generation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
