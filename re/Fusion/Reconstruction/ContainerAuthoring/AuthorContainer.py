import argparse
import collections
import hashlib
import io
import json
import lzma
import runpy
import struct
import sys
import uuid
import zipfile
import zlib
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
DESIGN = runpy.run_path(str(BASE.parent / 'DocumentAuthoring' / 'AuthorDesign.py'))
API = DESIGN['API']
TEXT = API['TOOLS']['encode_text']
SOFTWARE = (2706 << 50) | (1 << 38) | 17
CHANGE_TYPES = ('Appearance', 'Geometry', 'PhysicalMaterial', 'Properties', 'StructureChange', 'Transform')


def reference(identity, segment=None):
    if identity is None:
        return None
    value = {'entityId': identity}
    if segment is not None:
        value['segmentId'] = segment
    return value


class Segment:
    def __init__(self, kind, segment_id, neutron_type, extensions):
        self.kind = kind
        self.segment_id = segment_id
        self.neutron_type = neutron_type
        self.extensions = extensions
        self.codec = API['GraphCodec']({'classes': {}})
        self.names = {item['name'].removesuffix('MetaType'): item for item in self.codec.schema.values()}
        self.records = []
        self.roots = []

    def groups(self, name, fields):
        output = []
        consumed = set()
        for group in self.codec.groups(self.names[name]['identifier']):
            names = [member['name'] for member in self.codec.members(group)]
            missing = set(names) - set(fields)
            if missing:
                raise ValueError(name + ' missing ' + str(missing))
            consumed.update(names)
            output.append({'identifier': group['metatype_identifier'], 'fields': {key: fields[key] for key in names}})
        if set(fields) != consumed:
            raise ValueError(name + ' extra ' + str(set(fields) - consumed))
        return output

    def add(self, role, identity, name, fields, root='', subjects=(), split=None):
        groups = self.groups(name, fields)
        frame = {'rootId': root, 'hasSubjects': bool(subjects), 'subjects': list(subjects), 'hasNamedMetadata': False, 'namedMetadata': []}
        self.records.append({'role': role, 'identity': identity, 'primary': True, 'value': {'frame': frame, 'groups': groups[:split]}})
        if split is not None:
            self.records.append({'role': role, 'identity': identity, 'primary': False, 'value': {'frame': {'rootId': root}, 'groups': groups[split:]}})
        if root:
            self.roots.append(identity)

    def emit(self):
        self.records.sort(key=lambda record: (record['identity'], not record['primary']))
        classes = DESIGN['declarations'](self, self.records)
        codes = {entry['identifier'].upper(): code for code, entry in classes.items()}
        owners = {code: [] for code in classes}
        indices = {True: [], False: []}
        bulk = bytearray()
        for record in self.records:
            code = codes[record['value']['groups'][0]['identifier'].upper()]
            indices[record['primary']].append((record['identity'], len(bulk)))
            if record['primary']:
                owners[code].append(record['identity'])
            bulk.extend(TEXT(str(code)) + struct.pack('<Q', record['identity']) + API['emit_record'](self.codec, record['value'], record['primary']))
        meta = bytearray(TEXT(self.kind) + struct.pack('<I', self.segment_id) + TEXT(str(uuid.UUID(int=0)), True))
        meta.extend(struct.pack('<IIQ', 1234, 8, SOFTWARE) + TEXT(self.kind) + TEXT('Fusion') + struct.pack('<III', self.neutron_type, 0, len(classes)))
        for code, entry in classes.items():
            meta.extend(TEXT(entry['identifier']) + TEXT(entry['baseIdentifier']) + struct.pack('<I', entry['schemaVersion']) + TEXT(entry['namespace']))
            meta.extend(struct.pack('<I', len(owners[code])) + b''.join(struct.pack('<Q', value) for value in owners[code]))
        meta.extend(struct.pack('<I', len(self.roots)) + b''.join(struct.pack('<Q', value) for value in self.roots))
        for primary in (True, False):
            meta.extend(struct.pack('<I', len(indices[primary])) + b''.join(struct.pack('<QQ', *entry) for entry in indices[primary]))
        meta.extend(struct.pack('<QII', max(record['identity'] for record in self.records) + 1, 0, len(self.extensions)))
        for name, version in self.extensions.items():
            meta.extend(TEXT(name) + struct.pack('<I', version))
        return {'metadata': bytes(meta), 'bulk': bytes(bulk), 'model': {'kind': self.kind, 'segmentId': self.segment_id, 'classes': classes, 'roots': self.roots, 'records': self.records}}


def act_segment(design, snapshot_id):
    model = design['model']
    specification = model['specification']
    roles = dict(specification['actRoles'])
    next_id = max(roles.values()) + 1
    for role in ('table', 'components_root', 'instances_root', 'component_revision', 'instance_revision'):
        roles[role] = next_id
        next_id += 1
    segment_id = specification['actSegmentId']
    segment = Segment('FusionACTSegmentType', segment_id, 5, {'Application': 1, 'Server': 1})
    local = lambda role: reference(roles[role])
    external = lambda role: reference(model['roles'][role], specification['designSegmentId'])
    identifier = lambda role: str(segment_id) + '_' + str(roles[role])
    revision_map = lambda value: [{'key': key, 'value': value} for key in CHANGE_TYPES]
    entries = [segment.groups('ACTTableEntryValue', {'rActData': local(revision), 'tgtIdentifier': identifier(role)}) for role, revision in [('component', 'component_revision'), ('root_instance', 'instance_revision')]]
    segment.add('table', roles['table'], 'ACTTable', {'ACTTableEntries': entries, 'AssetRevGuid': snapshot_id, 'RevisionGuid': model['revisionGuid'], 'refdTables': [], 'revisionGuidForChangeType': revision_map(model['revisionGuid'])}, root='ACTTable')
    segment.add('components_root', roles['components_root'], 'ACTComponentsRoot', {'rootId': 'ACTComponentsRoot', 'rooted': [local('component')], 'rParent': None}, root='ACTComponentsRoot')
    segment.add('component', roles['component'], 'ACTComponent', {'ACTInstances': local('instances'), 'actIdentifier': identifier('component'), 'designComponent': external('component'), 'name': specification['title'], 'rParent': local('root_instance')})
    segment.add('component_revision', roles['component_revision'], 'RevGUIDACTDataMany', {'revGuidMap': revision_map(model['revisionGuid']), 'actIdentifier': identifier('component')})
    segment.add('instances', roles['instances'], 'ACTInstances', {'rDesignInstances': external('component_instances'), 'softDeletedInstances': [], 'children': [], 'rParent': local('component')})
    segment.add('instances_root', roles['instances_root'], 'ACTInstancesRoot', {'instancesMap': [{'key': 0, 'value': local('root_instance')}], 'nextInstanceId': 1, 'rootId': 'ACTInstancesRoot', 'rooted': [local('root_instance')], 'rParent': None}, root='ACTInstancesRoot')
    act_ref = segment.groups('ACTRefValue', {'actRefdTable': None, 'changeTypesToTrack': list(CHANGE_TYPES), 'crossAsset': False, 'owningEntity': local('root_instance'), 'rActData': None, 'refdEntity': local('component')})
    segment.add('root_instance', roles['root_instance'], 'ACTInstance', {'ACTRef': act_ref, 'actIdentifier': identifier('root_instance'), 'bSoftDeleted': False, 'designInstance': external('root_instance'), 'instanceId': 0, 'targetComponent': local('component'), 'rParent': None}, root='ACTInstanceRoot')
    segment.add('instance_revision', roles['instance_revision'], 'RevGUIDACTDataMany', {'revGuidMap': revision_map(str(uuid.uuid4())), 'actIdentifier': identifier('root_instance')})
    result = segment.emit()
    result['model']['roles'] = roles
    return result


def browser_segment(design):
    model = design['model']
    specification = model['specification']
    segment = Segment('FusionBrowserSegmentType', 2, 6, {'Application': 2, 'Server': 2})
    nodes = [
        ('component', 'FusionComponentInstanceBrowserEntry', 'root_instance', None, ''),
        ('settings', 'DocumentSettingsBrowserEntry', 'settings', 'component', ''),
        ('named_views', 'NamedViewsBrowserEntry', 'named_views', 'component', ''),
        ('named_lights', 'NamedLightsBrowserEntry', 'named_lights', 'component', ''),
        ('selection_groups', 'SelectionGroupsBrowserEntry', 'selection_groups', 'component', ''),
        ('contacts', 'ContactSetsBrowserEntry', 'contacts', 'component', ''),
        ('origin', 'OriginWorkGeometryBrowserEntry', 'origin', 'component', ''),
        ('motion_studies', 'MotionStudiesBrowserEntry', 'motion_studies', 'component', ''),
        ('joint_origins', 'JointOriginsBrowserEntry', 'joint_origins', 'component', ''),
        ('relationships', 'RelationshipsBrowserEntry', 'constraints', 'component', 'Ns::Comp::RelationshipsBrowserEntry'),
        ('joints', 'JointsBrowserEntry', 'constraints', 'relationships', 'JointsBrowserEntry'),
        ('rigid_groups', 'RigidGroupsBrowserEntry', 'constraints', 'relationships', 'Ns::Comp::RigidGroupsBrowserEntry'),
        ('tangent', 'TangentRelationshipsBrowserEntry', 'constraints', 'relationships', 'TangentRelationshipsBrowserEntry'),
        ('constraints', 'ConstraintsBrowserEntry', 'constraints', 'relationships', 'Ns::Comp::ConstraintsBrowserEntry'),
        ('bodies', 'FusionBodiesBrowserEntry', 'bodies', 'component', ''),
        ('cache_bodies', 'FusionBodiesBrowserEntry', 'cache_bodies', 'component', ''),
        ('canvases', 'CanvasesBrowserEntry', 'canvases', 'component', ''),
        ('annotations', 'AnnotationsBrowserEntry', 'annotations', 'component', ''),
        ('decals', 'DecalPatchesBrowserEntry', 'decals', 'component', ''),
        ('sketches', 'FusionSketchesBrowserEntry', 'sketches', 'component', ''),
        ('construction', 'FusionConstructionBrowserEntry', 'work_geometries', 'component', ''),
        ('eip_contexts', 'EIPContextsBrowserEntry', 'eip_contexts', 'component', ''),
        ('surface_groups', 'SurfaceGroupsBrowserEntry', 'surface_groups', 'component', ''),
        ('work_groups', 'WorkGeometryCustomGroupsBrowserEntry', 'work_groups', 'component', ''),
        ('sketch_groups', 'SketchCustomGroupsBrowserEntry', 'sketch_groups', 'component', ''),
        ('subd', 'SubDSurfaceNodesBrowserEntry', 'subd', 'component', ''),
        ('arrangements', 'ArrangementsBrowserEntry', 'arrangements', 'component', ''),
        ('units', 'UnitsBrowserEntry', 'units', 'settings', ''),
        ('structure_type', 'DocumentStructureTypeBrowserEntry', None, 'settings', 'Na::DocumentStructureTypeBrowserEntry'),
        ('pmi_settings', 'PMISettingsBrowserEntry', 'pmi_settings', 'settings', ''),
        ('thread_settings', 'ChangeThreadTypeBrowserEntry', 'thread_settings', 'settings', ''),
    ]
    roles = {'root': 200} | {node[0]: index + 201 for index, node in enumerate(nodes)}
    local = lambda role: reference(roles[role])
    external = lambda role: None if role is None else reference(model['roles'][role], specification['designSegmentId'])
    passive = [{'key': external(entity), 'value': local(role)} for role, name, entity, parent, string_id in nodes if not string_id]
    strings = collections.defaultdict(list)
    for role, name, entity, parent, string_id in nodes:
        if string_id:
            strings[entity].append({'key': string_id, 'value': local(role)})
    root_fields = {'ComponentInstance': external('root_instance'), 'autoExpandRootNode': True, 'passiveentries': passive, 'rootEntry': local('component'), 'stringentries': [{'key': external(entity), 'value': items} for entity, items in strings.items()], 'rParent': None}
    segment.add('root', roles['root'], 'FusionComponentBrowserRoot', root_fields, root='PersistBrowserRootId', split=3)
    observer_next = collections.defaultdict(int)
    for record in model['records']:
        for subject in record['value']['frame'].get('subjects', []):
            link = subject['subject']
            if link.get('segmentId', specification['designSegmentId']) == specification['designSegmentId']:
                observer_next[link['entityId']] = max(observer_next[link['entityId']], subject['indexInObserverVec'] + 1)
    for role, name, entity, parent, string_id in nodes:
        component_links = []
        if role == 'component':
            component_links = ['component', 'component_instances', 'overrides']
        elif role == 'structure_type':
            component_links = ['component_instances']
        elif role == 'pmi_settings':
            component_links = ['settings']
        subjects = []
        for subject_role in component_links + ([entity] if entity is not None else []):
            subject_id = model['roles'][subject_role]
            subjects.append({'subject': external(subject_role), 'indexInObserverVec': observer_next[subject_id]})
            observer_next[subject_id] += 1
        fields = {'AlwaysAddChild': True, 'ComponentInstance': [external(value) for value in component_links], 'MissingLinkReason': 2, 'bHasRefdEntry': False, 'children': [local(child[0]) for child in nodes if child[3] == role], 'entity': external(entity), 'flags': 1, 'hiddenChildren': [], 'parents': [] if parent is None else [local(parent)], 'root': local('root'), 'strEntityId': string_id, 'virtualParents': []}
        if role == 'component':
            fields.update(ComponentsFolderEntry=None, ACTInstance=reference(specification['actRoles']['root_instance'], specification['actSegmentId']))
        segment.add(role, roles[role], name, fields, subjects=subjects)
    result = segment.emit()
    result['model']['roles'] = roles
    return result


def versions(values):
    return struct.pack('<I', len(values)) + b''.join(TEXT(key) + struct.pack('<I', value) for key, value in values.items())


def root_manifest(model):
    output = bytearray(TEXT('3-2-0-0') + TEXT('FusionDocType'))
    for text in ('.f3d', model['documentTypeName'], model['documentTypeDescription'], model['documentId'], model['documentCurrentVersion']):
        output.extend(TEXT(text, True))
    output.extend(struct.pack('<IIQ', 1234, 20, SOFTWARE))
    output.extend(versions({'Application': 1, 'CAM': 4, 'ParaMesh': 8, 'SimCommon': 30005, 'SimFEACSObjects': 2, 'SimFluidDynamics': 2, 'SimStructuralAttributes': 10002}))
    output.extend(struct.pack('<IB', 0, 0) + TEXT(model['assetId'], True) + struct.pack('<I', 1))
    output.extend(TEXT(model['assetName'], True) + struct.pack('<IB', 0, 1) + TEXT('NA_EXPORT', True))
    return bytes(output)


def asset_manifest(model, segments):
    output = bytearray(b''.join(TEXT(model[key], True) for key in ('assetName', 'assetId', 'snapshotId')))
    output.extend(TEXT('FusionAssetType') + struct.pack('<I', 20))
    output.extend(versions({'Application': 139, 'ParaMesh': 13, 'Server': 36, 'VolField': 4}))
    output.extend(TEXT('Neutron3DAssetType') + struct.pack('<IBIIII', 0, 0, 0, 0, max(identity for identity, kind in segments) + 1, len(segments)))
    for segment_id, kind in segments:
        output.extend(struct.pack('<I', segment_id) + TEXT(kind) + TEXT(kind))
    return bytes(output)


def blank_png(width, height):
    def chunk(kind, payload):
        return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload))
    image = b''.join(b'\0' + bytes((242, 242, 242, 255)) * width for _ in range(height))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(image)) + chunk(b'IEND', b'')


def build_container(design, envelope=None, compression=zipfile.ZIP_STORED, directories=True, generated_parts=None):
    title = design['model']['specification']['title']
    model = {'title': title, 'documentTypeName': 'Fusion Document', 'documentTypeDescription': 'A Fusion Document', 'assetName': 'FusionAssetName', 'documentId': str(uuid.uuid4()), 'documentCurrentVersion': str(uuid.uuid4()), 'assetId': str(uuid.uuid4()), 'snapshotId': str(uuid.uuid4())}
    if envelope is not None:
        if any(key not in model for key in envelope):
            raise ValueError('Unsupported envelope field')
        model.update(envelope)
    act = act_segment(design, model['snapshotId'])
    browser = browser_segment(design)
    segment_types = [(design['model']['specification']['designSegmentId'], 'FusionDesignSegmentType'), (design['model']['specification']['actSegmentId'], 'FusionACTSegmentType'), (2, 'FusionBrowserSegmentType')]
    if len({value[0] for value in segment_types}) != 3:
        raise ValueError('Segment identities overlap')
    prefix = model['assetName'] + '[Active]/'
    members = {'Manifest.dat': root_manifest(model), 'Properties.dat': TEXT(''), prefix + 'Manifest.dat': asset_manifest(model, segment_types)}
    for (_, kind), result in zip(segment_types, (design, act, browser)):
        members[prefix + kind + '1/MetaStream.dat'] = result['metadata']
        members[prefix + kind + '1/BulkStream.dat'] = result['bulk']
    for name, payload in (generated_parts or {}).items():
        parts = name.split('/')
        if len(parts) != 2 or parts[0] not in ('Breps.BlobParts', 'ProteinAssets.BlobParts', 'Images.BlobParts') or parts[1] in ('', '.', '..') or '\\' in name or '\0' in name:
            raise ValueError('Invalid generated blob part name')
        if not isinstance(payload, bytes):
            raise TypeError('Generated blob part must be encoded bytes')
        members[prefix + name] = payload
    members[prefix + 'Previews/big.png'] = blank_png(256, 256)
    members[prefix + 'Previews/small.png'] = blank_png(64, 64)
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression) as archive:
        if directories:
            folders = sorted({name[:index + 1] for name in members for index, value in enumerate(name) if value == '/'} | {prefix + 'Breps.BlobParts/'}, key=lambda value: (value.count('/'), value))
            for name in folders:
                info = zipfile.ZipInfo(name, date_time=(2026, 11, 12, 0, 0, 0))
                info.external_attr = (0o40755 << 16) | 0x10
                archive.writestr(info, b'')
        for name, data in members.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 12, 0, 0, 0))
            info.compress_type = compression
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return {'archive': output.getvalue(), 'members': members, 'model': model, 'act': act, 'browser': browser}


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--generated-design', type=Path)
    source.add_argument('--specification', type=Path)
    parser.add_argument('--envelope', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.generated_design:
        directory = arguments.generated_design
        design = {'metadata': (directory / 'MetaStream.dat').read_bytes(), 'bulk': (directory / 'BulkStream.dat').read_bytes(), 'model': json.loads((directory / 'AuthoredModel.json').read_bytes() if (directory / 'AuthoredModel.json').exists() else lzma.decompress((directory / 'AuthoredModel.json.xz').read_bytes()))}
        design_source = {'kind': 'independently authored intermediate', 'path': str(directory)}
    else:
        design = DESIGN['build_document'](json.loads(arguments.specification.read_text()))
        design_source = {'kind': 'semantic specification', 'path': str(arguments.specification)}
    envelope = None if arguments.envelope is None else json.loads(arguments.envelope.read_text())
    result = build_container(design, envelope)
    arguments.output.mkdir(parents=True, exist_ok=True)
    candidate = arguments.output / 'AuthoredParameter.f3d'
    candidate.write_bytes(result['archive'])
    for kind in ('act', 'browser'):
        for key, filename in [('metadata', 'MetaStream.dat'), ('bulk', 'BulkStream.dat')]:
            (arguments.output / (kind.capitalize() + filename)).write_bytes(result[kind][key])
        (arguments.output / (kind.capitalize() + 'Model.json')).write_text(json.dumps(result[kind]['model'], indent=2) + '\n')
    (arguments.output / 'EnvelopeModel.json').write_text(json.dumps(result['model'], indent=2) + '\n')
    report = {'schema': 'FusionAuthoredContainer/1', 'status': 'authored_native_acceptance_pending', 'candidate': str(candidate), 'sha256': hashlib.sha256(result['archive']).hexdigest(), 'designSource': design_source, 'sourceArchive': None, 'runtimeVendorTemplate': None, 'members': [{'name': name, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for name, data in result['members'].items()], 'omissions': ['configuration: no configuration triggers', 'protein: empty partName and no material references', 'OGS: empty partName', 'BRep: no bodies']}
    (arguments.output / 'Generation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
