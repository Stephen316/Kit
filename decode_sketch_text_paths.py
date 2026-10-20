"""Observed AlongPath/FitOnPath text with explicit owned Line/Arc paths.

The shared reader validates source text and reciprocal text/height bindings.
Controller matrices are retained as uninterpreted caches, never used to identify
source curves, reconstruct glyphs or infer Above/Along/Fit controls.
"""

import math
import struct

from decode_sketch import constraint_prefix, numbers, reference
from decode_sketch_texts import OPAQUE_PREFIX, decode_sketch_texts


CONTROLLER = '9D30FCDC-EA07-4141-93E2-918B1A59E962'
PATH_TAIL_PREFIX = bytes.fromhex('010000000090010000010000000100000000010000000000000000000000000000803f0000803f0000000000')
CURVE_TYPES = {'Line': ('DCA267ED-D615-4934-B64F-AD805E8003E2', 337),
               'Arc': ('F0130424-8B7E-4092-93C9-1CA807482534', 348)}


def decode_path_text_controls(prefix, flags, tail):
    if (len(prefix) != 25 or prefix[0] not in (0, 1) or prefix[9:] != OPAQUE_PREFIX[9:]
            or len(flags) != 7 or flags[4:] != b'\0'*3
            or len(tail) != 55 or tail[:44] != PATH_TAIL_PREFIX):
        raise ValueError('Unobserved path Text source controls or layout suffix')
    multiplier = struct.unpack_from('<d', prefix, 1)[0]
    spacing = (multiplier-1.)*100.
    alignment = struct.unpack_from('<I', flags, 0)[0]
    if (not math.isfinite(multiplier) or not math.isfinite(spacing) or multiplier < 1.
            or alignment not in (1, 3)):
        raise ValueError('Unobserved path Text spacing/alignment')
    return {'text_properties': {'text_style': 0, 'bold': False, 'italic': False, 'native_font_weight': 400,
                                'text_style_status': 'Captured plain path Text with native weight400 and unset italic flag; other path styles unverified',
                                'underline': None, 'is_horizontal_flip': None, 'is_vertical_flip': None},
            'definition_properties': {'is_above_path': bool(prefix[0]),
                                      'horizontal_alignment': {1: 0, 3: 1}[alignment],
                                      'native_horizontal_alignment': alignment,
                                      'character_spacing_percent': spacing,
                                      'native_character_spacing_multiplier': multiplier,
                                      'vertical_alignment': None}}


def decode_path_text_definition(data, records, features, text_record, sketch, layout_marker):
    if layout_marker not in (0, 1):
        raise ValueError('Unsupported path Text source layout marker')
    controllers = []
    for record in records:
        if record.class_guid != CONTROLLER or not record.is_primary:
            continue
        body = data[record.body:record.end]
        inputs, props, cursor = constraint_prefix(body)
        if text_record.object_id in inputs:
            controllers.append((record, body, inputs, props, cursor))
    if len(controllers) != 1:
        raise ValueError('Path Text controller missing or ambiguous')
    record, body, inputs, props, cursor = controllers[0]
    if (len(inputs) != 2 or inputs[1] != text_record.object_id or inputs[0] == inputs[1]
            or props != {'EntityGenesis': 2} or body[cursor] != 0
            or reference(body, cursor+1) != text_record.object_id):
        raise ValueError('Unsupported path Text controller inputs/source links')
    count = struct.unpack_from('<I', body, cursor+12)[0]
    if not 1 <= count <= 100000 or len(body) != cursor+51+132*count:
        raise ValueError('Unsupported path Text counted transform-cache framing')
    matrices = []
    for index in range(count):
        offset = cursor+16+132*index
        if struct.unpack_from('<I', body, offset)[0] != 16:
            raise ValueError('Unsupported path Text cached matrix element count')
        matrices.append(numbers(body, offset+4, 16))
    position = cursor+16+132*count
    if (reference(body, position) != sketch['sketch_object_id']
            or body[position+11:position+19] != bytes.fromhex('0000000000020000')
            or struct.unpack_from('<I', body, position+19)[0] != 1
            or reference(body, position+23) != inputs[0] or body[position+34] != 0):
        raise ValueError('Path Text owner or repeated curve reference disagrees')
    curves = [g for g in sketch.get('geometry', []) if g['object_id'] == inputs[0]
              and g['kind'] in CURVE_TYPES and g['sketch_object_id'] == sketch['sketch_object_id']]
    if len(curves) != 1:
        raise ValueError('Path Text explicit source curve missing, unsupported or ambiguous')
    curve = curves[0]
    guid, size = CURVE_TYPES[curve['kind']]
    sources = [r for r in records if r.is_primary and r.object_id == inputs[0] and r.class_guid == guid]
    if len(sources) != 1:
        raise ValueError('Path Text source curve class/identity unresolved')
    source = sources[0]
    payload = data[source.body:source.end]
    if (len(payload) != size or source.start != curve['record_offset']
            or reference(payload, len(payload)-11) != sketch['sketch_object_id']):
        raise ValueError('Path Text source cache/owner disagrees with decoded curve')
    path = {'curve_object_id': curve['object_id'], 'curve_entity_tag': curve['entity_tag'], 'kind': curve['kind'],
            'sketch_object_id': sketch['sketch_object_id'], 'sketch_name': sketch['name'],
            'record_offset': source.start,
            'coordinate_system': 'sketch-local', 'coordinate_units': 'cm',
            'association': 'Controller input and repeated path reference select typed curve cache with matching explicit sketch owner'}
    for key in ('start_cm', 'end_cm', 'center_cm', 'radius_cm', 'normal', 'reference_axis',
                'start_angle_radians', 'end_angle_radians'):
        if key in curve:
            path[key] = curve[key]
    result = {'kind': 'FitOnPathTextDefintion' if layout_marker else 'AlongPathTextDefinition',
              'controller_object_id': record.object_id, 'source_layout_marker': layout_marker,
              'path': path, 'cached_transform_count': count, 'uninterpreted_cached_transform_values': matrices,
              'cache_status': 'Counted finite sixteen-value caches retained; character/glyph mapping and matrix frame semantics unclaimed',
              'status': 'Explicit path/Text dependency and reciprocal source/sketch references; source flags decode layout/above/alignment/spacing'}
    if layout_marker:
        result.update(horizontal_alignment=None, character_spacing_percent=None,
                      spacing_status='Fit mode has no alignment/spacing getters; raw stored source controls retained without claiming activity')
    else:
        result['spacing_status'] = 'Observed nonnegative percentage from native multiplier:1->0%,1.2->20%; right alignment/negative spacing unverified'
    return result


def decode_sketch_text_paths(data, records, features):
    result = decode_sketch_texts(data, records, features, controls_decoder=decode_path_text_controls,
                                 definition_decoder=decode_path_text_definition)
    result['scope'] = 'Observed editable AlongPath/FitOnPath Text on explicit Line/Arc source; source/bindings shared, glyph regeneration unavailable'
    accepted = []
    for text in result['texts']:
        definition = text['definition']
        if (definition['source_layout_marker'] == 1
                and (not definition['is_above_path'] or definition['native_horizontal_alignment'] != 1
                     or definition['native_character_spacing_multiplier'] != 1.)):
            result['unresolved'].append({'object_id': text['object_id'], 'class_guid': text['class_guid'],
                                         'record_offset': text['record_offset'],
                                         'reason': 'Only captured Above Fit text with default stored alignment/spacing supported'})
            continue
        text['scope'] = result['scope']
        accepted.append(text)
    result['texts'] = accepted
    return result
