import hashlib
import json
import runpy
import struct
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
API = runpy.run_path(str(BASE.parent / 'ReflectedFeatures.py'))
SOURCES = (
    're/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d',
    're/Fusion/LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d',
)
PREFIX = 'FusionAssetName[Active]/OGS.BlobFolder/OGS/DefaultScene/'


class Unresolved(Exception):
    pass


class Reader:
    def __init__(self, data, offset=0):
        self.data = data
        self.offset = offset
        self.fields = []
        self.handles = {}
        self.first_group = True

    def value(self, name, kind, count=1):
        start = self.offset
        if kind == 'id64':
            end = start + 8
            value = struct.unpack_from('>Q', self.data, start)[0]
        elif kind == 'utf16':
            size = struct.unpack_from('<I', self.data, start)[0]
            end = start + 4 + size * 2
            if end > len(self.data):
                raise Unresolved(f'{name}: string exceeds stream')
            value = self.data[start + 4:end].decode('utf-16le')
        else:
            code = {'u32': 'I', 'u64': 'Q', 'i32': 'i', 'bool': '?', 'f32': 'f', 'f64': 'd'}[kind]
            end = start + struct.calcsize('<' + code) * count
            values = struct.unpack_from('<' + code * count, self.data, start)
            value = values[0] if count == 1 else list(values)
            if kind == 'bool' and self.data[start] not in (0, 1):
                raise Unresolved(f'{name}: noncanonical bool at {start}')
        self.offset = end
        self.fields.append({'offset': start, 'end': end, 'name': name, 'type': kind, 'count': count, 'value': value})
        return value

    def text(self, name, expected=None):
        value = self.value(name, 'utf16')
        if expected is not None and value != expected:
            raise Unresolved(f'{name}: expected {expected}, found {value}')
        return value

    def flag(self, name):
        return self.value(name, 'bool')

    def world(self, name='World', class_name=None, root=False):
        class_name = class_name or self.text(name + '.InterfaceID')
        if class_name not in ('ARenderList', 'SingleNodeWorld'):
            raise Unresolved(f'{name}: unsupported world {class_name}')
        self.value(name + '.RevisionId', 'u32')
        self.value(name + '.PublishMode', 'i32')
        index = 0
        while True:
            child = name + f'.Nodes[{index}]'
            type_name = self.text(child + '.InterfaceID')
            if type_name == 'WorldSerializerEndMark':
                break
            if type_name == 'GroupNode':
                self.group(child)
            elif type_name == 'GeometryNode':
                self.geometry(child)
            elif type_name == 'FTextNode':
                self.text_node(child)
            else:
                raise Unresolved(f'{child}: serializer {type_name} not yet decoded')
            index += 1
        if class_name == 'ARenderList' and not root:
            self.flag(name + '.Accelerate')

    def group(self, name):
        handle = self.text(name + '.ObjectId')
        if handle in self.handles:
            return
        self.handles[handle] = 'GroupNode'
        if self.first_group:
            self.first_group = False
            size = self.value('SerializationData.Size', 'u32')
            for index in range(size):
                self.text(f'SerializationData.Versions[{index}].InterfaceID')
                self.value(f'SerializationData.Versions[{index}].Version', 'u32')
            self.text('SerializationData.EnvironmentVersion')
        if self.flag(name + '.HasWorldMatrix'):
            self.value(name + '.WorldMatrix', 'f32', 16)
        for prop in ('ClippingPlaneSave', 'StyleGraph', 'LocalGraphicScheme'):
            if self.flag(name + '.' + prop):
                raise Unresolved(f'{name}.{prop}: linked object not yet decoded')
        if not self.flag(name + '.NoCulling'):
            self.value(name + '.WorldBox', 'f64', 6)
        if self.flag(name + '.SaveWorld'):
            kind = self.value(name + '.SerializationType', 'u32')
            if kind == 1:
                self.brep_body(name + '.Body')
            elif kind == 3:
                self.sketch_world(name + '.Sketch')
            elif kind:
                raise Unresolved(f'{name}: custom world SerializationType {kind} not yet decoded')
            elif self.flag(name + '.World.ObjectSaved'):
                self.world(name + '.World')
        kind = self.value(name + '.NodeDataType', 'u32')
        self.quick_node(name + '.NodeData', kind)

    def quick_node(self, name, kind):
        if kind in (2, 3, 4, 5, 6, 7):
            self.node_data(name)
            if kind == 4:
                if self.flag(name + '.IsXRef'):
                    self.value(name + '.ACTEntityID', 'id64')
                self.value(name + '.InstanceID', 'u32')
        elif kind:
            raise Unresolved(f'{name}: quick NodeDataType {kind} not yet decoded')

    def body_child(self, name):
        if self.flag(name + '.HasWorldMatrix'):
            self.value(name + '.WorldMatrix', 'f32', 16)
        for prop in ('ClippingPlaneSave', 'StyleGraph', 'LocalGraphicScheme'):
            if self.flag(name + '.' + prop):
                raise Unresolved(f'{name}.{prop}: linked object not yet decoded')
        kind = self.value(name + '.NodeDataType', 'u32')
        self.quick_node(name + '.NodeData', kind)

    def lod_node(self, name):
        kind = self.value(name + '.NodeDataType', 'u32')
        self.quick_node(name + '.NodeData', kind)
        lods = self.value(name + '.HasLODs', 'u32')
        if lods:
            if lods & (lods - 1):
                raise Unresolved(f'{name}: multiple populated LODs not qualified')
            item_type = self.value(name + '.DisplayItemType', 'u32')
            if item_type:
                raise Unresolved(f'{name}: display item {item_type} not yet decoded')
            if self.flag(name + '.RenderGeom.ObjectSaved'):
                self.mesh_value(name + '.RenderGeom')
        self.value(name + '.WorldBox', 'f64', 6)
        self.flag(name + '.UseClosestLOD')

    def mesh_value(self, name):
        start = self.offset
        kind = self.text(name + '.InterfaceID')
        if kind == 'FatPointMesh':
            self.value(name + '.Width', 'i32')
            self.value(name + '.Height', 'i32')
            self.value(name + '.BBoxSize', 'f32', 3)
        elif kind == 'OgsSimpleMesh':
            self.offset = start
            self.fields.pop()
            self.mesh()
        else:
            raise Unresolved(f'{name}: unqualified mesh {kind}')

    def sketch_world(self, name):
        if self.flag(name + '.HasFaces'):
            self.brep_body(name + '.Body')
        lod_count = self.value(name + '.LODGeoNodeCount', 'i32')
        regular = self.value(name + '.RegularNodeCount', 'i32')
        for index in range(lod_count):
            self.lod_node(name + f'.LODNodes[{index}]')
        if regular:
            raise Unresolved(f'{name}: regular sketch nodes not yet decoded')
        if self.value(name + '.NoCullingNodeCount', 'i32'):
            raise Unresolved(f'{name}: nonculling sketch nodes not yet decoded')

    def brep_body(self, name):
        if self.flag(name + '.ValidBody'):
            self.body_child(name + '.Edges')
            count = self.value(name + '.EdgesCount', 'u32')
            for index in range(count):
                self.lod_node(name + f'.Edges.Nodes[{index}]')
            self.body_child(name + '.Faces')
            count = self.value(name + '.FacesCount', 'u32')
            for index in range(count):
                self.lod_node(name + f'.Faces.Nodes[{index}]')
        if self.flag(name + '.HasModelBox'):
            self.value(name + '.ModelBox', 'f64', 6)

    def node_data(self, name, quick=True):
        self.value(name + '.NodeType', 'u32')
        if not quick:
            self.text(name + '.RenderNode')
        attributes = self.value(name + '.AttributeType', 'i32')
        if attributes == 2:
            self.attributes(name + '.Attributes')
        elif attributes == 3:
            self.attributes_ex(name + '.Attributes')
        elif attributes not in (0, 1):
            raise Unresolved(f'{name}: AttributeType {attributes} not yet decoded')
        status = self.value(name + '.EntityStatus', 'i32')
        if status in (1, 2):
            self.value(name + '.SegmentId', 'u32')
            self.value(name + '.EntityID', 'id64')
        elif status != 0:
            raise Unresolved(f'{name}: unqualified entity status {status}')
        self.value(name + '.Qualifier', 'f64')
        if self.flag(name + '.ClientTypeNameSaved'):
            self.text(name + '.ClientTypeName')
        if self.flag(name + '.SubClientTypeNameSaved'):
            self.text(name + '.SubClientTypeName')
        self.value(name + '.SerializationID', 'f64')
        self.value(name + '.DoubleSided', 'u32')
        self.value(name + '.CyclingColor', 'f32', 4)
        self.value(name + '.ConsolidationFlags', 'u32')
        self.value(name + '.ImmediateConsolidationFlags', 'i32')
        self.value(name + '.RenderNodeFlags', 'u32')
        self.value(name + '.SceneInfoFlags', 'u32')

    def render_node(self, name):
        handle = self.text(name + '.ObjectId')
        if handle in self.handles:
            return
        self.handles[handle] = 'GeometryNode'
        if self.flag(name + '.HasWorldMatrix'):
            self.value(name + '.WorldMatrix', 'f32', 16)
        for key in ('ClippingPlane', 'StyleGraph', 'Billboard', 'LocalGraphicScheme'):
            if self.flag(name + '.' + key):
                raise Unresolved(f'{name}: nonempty {key} not yet decoded')
        if self.flag(name + '.Entity.ObjectSaved'):
            self.text(name + '.Entity.InterfaceID', 'NodeData')
            self.node_data(name + '.Entity', quick=False)

    def geometry(self, name):
        self.render_node(name)
        if self.flag(name + '.RenderGeom.ObjectSaved'):
            self.mesh()
        self.value(name + '.WorldBox', 'f64', 6)
        if self.flag(name + '.EffectInstance.ObjectSaved'):
            raise Unresolved(f'{name}: EffectInstance not yet decoded')

    def text_node(self, name):
        self.render_node(name)
        self.value(name + '.WorldMatrix', 'f32', 16)
        self.value(name + '.Envelop', 'f32', 2)
        if self.flag(name + '.HasTextData'):
            self.text(name + '.TextData')
        self.value(name + '.GlobalAlignment', 'i32')
        self.value(name + '.GlobalEscapement', 'f32')
        for kind in ('TextStyle', 'ParagraphStyle', 'BlockStyle'):
            self.text_style(name + '.' + kind, kind)
        self.value(name + '.AnchorPoint', 'f32', 2)
        self.value(name + '.Priority', 'i32')

    def text_style(self, name, kind):
        if not self.flag(name + '.ObjectSaved'):
            return
        self.text(name + '.InterfaceID', kind)
        handle = self.text(name + '.ObjectId')
        if handle in self.handles:
            return
        self.handles[handle] = kind
        if kind == 'ParagraphStyle':
            for member in ('LeftIndent', 'RightIndent', 'FirstLineIndent'):
                self.value(name + '.' + member, 'f32')
            if self.value(name + '.TabStopCount', 'u32'):
                raise Unresolved(f'{name}: nonempty tab stops not qualified')
            fields = [('LineSpace', 'f32', 1), ('Ascent', 'f32', 1), ('Descent', 'f32', 1), ('AlignmentType', 'i32', 1), ('LineSpaceType', 'i32', 1)]
        elif kind == 'BlockStyle':
            fields = [(member, 'i32', 1) for member in ('Baseline direction', 'Flow direction', 'Baseline alignment', 'Flow alignment')] + [('Escapement', 'f32', 1), ('IsHorizontalBaseline', 'bool', 1)]
        else:
            self.text(name + '.Typeface')
            fields = [('Charset', 'i32', 1), ('Pitch', 'i32', 1), ('Family', 'i32', 1), ('IsSHX', 'bool', 1), ('Color', 'f32', 4), ('Height', 'f32', 1), ('Weight', 'i32', 1), ('WidthFactor', 'f32', 1), ('CharSacingFactor', 'f32', 1), ('Italic', 'bool', 1), ('ObliqueAngle', 'f32', 1), ('Underline', 'bool', 1), ('Strikethrough', 'bool', 1), ('Overline', 'bool', 1), ('BaselineOffset', 'f32', 1), ('BackgroundColor', 'f32', 4), ('Orientation', 'f32', 1)]
        for member, wire, count in fields:
            self.value(name + '.' + member, wire, count)

    def attributes(self, name):
        self.value(name + '.HasAttributes', 'u32')
        self.value(name + '.mRemoveAttributes', 'u32')
        count = self.value(name + '.AppendTypeCount', 'u32')
        for index in range(count):
            self.value(name + f'.AppendType[{index}]', 'u32')
        count = self.value(name + '.AttributeCount', 'i32')
        for index in range(count):
            child = name + f'.Items[{index}]'
            kind = self.text(child + '.AttrName')
            self.attribute(child, kind)

    def attributes_ex(self, name):
        self.attributes(name)
        if self.flag(name + '.TargetExternalNode'):
            self.value(name + '.EntityID', 'id64')
            self.value(name + '.SegmentID', 'u32')
        else:
            self.text(name + '.Node')
        count = self.value(name + '.AttributeSetCount', 'i32')
        for index in range(count):
            child = name + f'.Sets[{index}]'
            specific = self.flag(child + '.IsTypeAttribute')
            self.attributes(child)
            if specific:
                apply = self.value(child + '.ApplyTypeCount', 'u32')
                for entry in range(apply):
                    self.value(child + f'.ApplyType[{entry}]', 'u32')

    def attribute(self, name, kind):
        self.value(name + '.Priority', 'i32')
        self.flag(name + '.WinTies')
        basic = {
            'HWSelectionPostProcessingAttribute': [],
            'DepthPriorityAttribute': [('DepthPriority', 'i32', 1)],
            'VisibilityAttribute': [('Visibility', 'bool', 1)],
            'TransformAttribute': [('Transform', 'f32', 16), ('Absolute', 'bool', 1)],
            'FColorEffectAttribute': [('Color', 'f32', 4)],
            'GroupAttribute': [('GroupID', 'i32', 1)],
            'OrderInTransparentGroupAttribute': [('OrderInTransparentGroup', 'i32', 1)],
            'BillBoardAttribute': [('Style', 'i32', 1), ('Anchor', 'f32', 3), ('Axis', 'f32', 3), ('Compensation', 'f32', 3), ('FlipVisibility', 'i32', 1)],
            'PixelScaleAttribute': [('ScreenSpaceSize', 'f64', 1), ('ModelSpaceSize', 'f64', 1), ('ScaleCenter', 'f32', 3)],
            'PixelScaleTranslationAttribute': [('ScreenSpaceDistance', 'f64', 1), ('Translation', 'f32', 3)],
        }
        if kind in basic:
            for member, wire, count in basic[kind]:
                self.value(name + '.' + member, wire, count)
        elif kind == 'SelectabilityAttribute':
            self.flag(name + '.Selectability')
            self.value(name + '.SelectionPriority', 'i32')
            if self.flag(name + '.AlphaImageSelectionQualifier.ObjectSaved'):
                raise Unresolved(f'{name}: alpha image qualifier not yet decoded')
        elif kind == 'FOccludedEffectAttribute':
            self.value(name + '.Color', 'f32', 4)
            if self.flag(name + '.ImagePartNameSaved'):
                self.text(name + '.ImagePartName')
            if self.flag(name + '.hasPath'):
                self.text(name + '.Path')
            self.value(name + '.VisibleOpacity', 'f32')
            self.value(name + '.OccludedOpacity', 'f32')
        elif kind == 'FLineStyleAttribute':
            self.value(name + '.Weight', 'f32')
            self.value(name + '.Space', 'i32')
            if self.flag(name + '.LinePatternNameSaved'):
                self.text(name + '.LinePatternName')
            self.value(name + '.XScale', 'f32')
            self.value(name + '.YScale', 'f32')
        elif kind == 'TextureMappingAttribute':
            if self.flag(name + '.TextureMappingSaved'):
                self.text(name + '.AssetName')
                self.value(name + '.SegmentId', 'u32')
                self.value(name + '.EntityID', 'id64')
                self.texture_cache(name + '.Cache')
        elif kind == 'FPrioritizedProteinAttribute':
            self.text(name + '.AssetReference')
            self.value(name + '.Category', 'u32')
        else:
            raise Unresolved(f'{name}: attribute {kind} not yet decoded')

    def texture_cache(self, name):
        self.flag(name + '.CacheIsLayered')
        self.cache_data(name + '.Primary')
        if self.flag(name + '.CacheHasSecondary'):
            self.cache_data(name + '.Secondary')

    def cache_data(self, name):
        mode = self.value(name + '.Mode', 'i32')
        self.value(name + '.Axis', 'f64', 3)
        self.value(name + '.BBox', 'f64', 6)
        self.value(name + '.BakedTfm', 'f64', 16)
        self.value(name + '.MappingTfm', 'f64', 16)
        if mode == 4:
            self.flag(name + '.CylindricalCap')
            self.flag(name + '.CylindricalCapSquare')
        elif mode == 6:
            self.value(name + '.ProceduralWoodOrigin', 'f64', 3)
            self.value(name + '.ProceduralWoodBoardFaceAxis', 'f64', 3)
        elif mode not in (0, 1, 2, 3, 5):
            raise Unresolved(f'{name}: unqualified cache mode {mode}')

    def vertex_format(self, name):
        if not self.flag(name + '.ObjectSaved'):
            return None
        self.text(name + '.InterfaceID', 'VertexFormat')
        handle = self.text(name + '.ObjectId')
        if handle in self.handles:
            return self.handles[handle]
        count = self.value(name + '.VertexFormatTableCount', 'i32')
        fields = []
        for index in range(count):
            values = self.value(name + f'.VertexField[{index}]', 'i32', 6)
            fields.append(dict(zip(('typeEnum', 'usageEnum', 'wordOffset', 'streamIndex', 'usageIndex', 'instanceControl'), values)))
        self.handles[handle] = fields
        return fields

    def mesh(self):
        self.text('Mesh.InterfaceID', 'OgsSimpleMesh')
        self.value('Mesh.Modelbox', 'f32', 6)
        primitive = self.value('Mesh.PrimitiveType', 'i32')
        buffers = []
        fields = None
        if self.flag('Mesh.VertexBuffer.ObjectSaved'):
            self.flag('Mesh.VertexBuffer.DynamicResource')
            fields = self.vertex_format('Mesh.VertexBuffer.VertexFormat')
            streams = self.value('Mesh.VertexBuffer.StreamCount', 'i32')
            if streams != 1:
                raise Unresolved(f'multiple vertex streams not qualified: {streams}')
            values = self.value('Mesh.VertexBuffer.Props', 'i32', 3)
            buffers.append({'kind': 'vertices', 'stream': values[0], 'offset': values[1], 'length': values[2], 'format': fields})
        if self.flag('Mesh.IndexBuffer.ObjectSaved'):
            self.text('Mesh.IndexBuffer.InterfaceID', 'AIndexBuffer')
            handle = self.text('Mesh.IndexBuffer.ObjectId')
            if handle in self.handles:
                buffers.append(self.handles[handle])
            else:
                self.flag('Mesh.IndexBuffer.DynamicResource')
                values = self.value('Mesh.IndexBuffer.Props', 'i32', 4)
                record = {'kind': 'indices', 'stream': values[0], 'offset': values[1], 'length': values[2], 'is16Bit': bool(values[3])}
                if values[3] not in (0, 1):
                    raise Unresolved('invalid index width flag')
                self.handles[handle] = record
                buffers.append(record)
        self.flag('Mesh.Planarity')
        return {'primitiveType': primitive, 'buffers': buffers}


def occurrences(data, value):
    encoded = struct.pack('<I', len(value)) + value.encode('utf-16le')
    offset = data.find(encoded)
    while offset >= 0:
        yield offset
        offset = data.find(encoded, offset + 1)


def decode_buffers(records, mesh):
    spans = []
    for record in records:
        for buffer in record.get('buffers', []):
            start, size = buffer['offset'], buffer['length']
            if buffer['stream'] != 0 or start < 0 or size < 0 or start + size > len(mesh):
                raise Unresolved('invalid mesh stream descriptor')
            row = dict(buffer, end=start + size)
            if buffer['kind'] == 'indices':
                code, width = ('H', 2) if buffer['is16Bit'] else ('I', 4)
                if size % width:
                    raise Unresolved('partial index')
                row['values'] = list(struct.unpack_from('<' + code * (size // width), mesh, start))
            else:
                fields = buffer['format']
                if not fields or any(field['typeEnum'] not in (0, 1, 2, 3) for field in fields):
                    row['unresolved'] = 'vertex format type not yet qualified'
                elif any(field['instanceControl'] or field['streamIndex'] or field['usageIndex'] for field in fields):
                    row['unresolved'] = 'nonzero vertex stream, usage index or instance control not qualified'
                else:
                    width = sum(field['typeEnum'] + 1 for field in fields)
                    if size % (width * 4):
                        raise Unresolved('partial vertex')
                    values = struct.unpack_from('<' + 'f' * (size // 4), mesh, start)
                    row['vertices'] = [list(values[index:index + width]) for index in range(0, len(values), width)]
                    row['semanticStatus'] = 'qualified noninstanced sampled vertex profile; parent ownership checked against the complete world parse'
                    row['components'] = [{'name': {0: 'POSITION', 1: 'NORMAL', 2: 'TEXCOORD0'}.get(field['usageEnum'], 'unqualified'), 'wordOffset': field['wordOffset'], 'width': field['typeEnum'] + 1} for field in fields]
            spans.append(row)
    ranges = sorted({(row['offset'], row['end']) for row in spans})
    cursor = 0
    gaps = []
    for start, end in ranges:
        if start > cursor:
            gaps.append([cursor, start])
        cursor = max(cursor, end)
    if cursor < len(mesh):
        gaps.append([cursor, len(mesh)])
    return {'ranges': spans, 'unaddressedSpans': gaps, 'allBytesAddressed': not gaps, 'fullSemanticQualification': False}


def inspect(path):
    world = API['archive_member'](path, PREFIX + 'world')
    mesh = API['archive_member'](path, PREFIX + 'stream_mesh_000')
    prefix = Reader(world)
    try:
        prefix.world(root=True)
        reason = None if prefix.offset == len(world) else 'Unexpected trailing world bytes'
    except Unresolved as error:
        reason = str(error)
    reader = Reader(world)
    meshes = []
    for start in occurrences(world, 'OgsSimpleMesh'):
        reader.offset = start
        reader.fields = []
        try:
            row = reader.mesh()
            row.update({'offset': start, 'end': reader.offset, 'fields': list(reader.fields)})
        except Unresolved as error:
            row = {'offset': start, 'end': reader.offset, 'unresolved': str(error), 'fields': list(reader.fields)}
        meshes.append(row)
    return {'source': str(path.relative_to(ROOT)), 'sourceSha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'world': {'size': len(world), 'sha256': hashlib.sha256(world).hexdigest(), 'decodedPrefixEnd': prefix.offset, 'fields': prefix.fields, 'unresolved': reason, 'unresolvedSpan': [prefix.offset, len(world)], 'isolatedMeshCandidates': meshes, 'isolatedCandidateQualification': 'Candidate offsets checked against mesh interface fields in the complete parent scene parse', 'parentOwnedMeshOffsets': [field['offset'] for field in prefix.fields if field['name'] == 'Mesh.InterfaceID'], 'meshCandidatesMatchParent': {row['offset'] for row in meshes} == {field['offset'] for field in prefix.fields if field['name'] == 'Mesh.InterfaceID'}}, 'mesh': {'size': len(mesh), 'sha256': hashlib.sha256(mesh).hexdigest(), **decode_buffers(meshes, mesh)}}


def main():
    result = {'scope': 'Complete named-value decoding of two qualified controls; no native acceptance of emitted graphics claimed', 'sources': [inspect(ROOT / source) for source in SOURCES]}
    (BASE / 'DecodedSamples.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps([{'source': row['source'], 'prefixEnd': row['world']['decodedPrefixEnd'], 'reason': row['world']['unresolved'], 'meshCandidates': len(row['world']['isolatedMeshCandidates']), 'meshGaps': row['mesh']['unaddressedSpans']} for row in result['sources']], indent=2))


if __name__ == '__main__':
    main()
