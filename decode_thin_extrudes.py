"""Observed additive Thin Extrude controls using the shared extrusion parser.

Wall sides are extrusion extent sides. No wall offset geometry, solid operation
or topology is regenerated; explicit profile/body references remain provenance.
"""
import math
import struct

from decode_body_selections import ANCHOR, decode_body_selections
from decode_extrude import decode_extrude, optional_reference
from decode_parameters import decode_stream
from decode_profile_selections import resolve_sketch_profiles
from decode_selection import native_proxy_references, resolve_single_sketch_curve
from decode_sketch import reference

EXTRUDE = 'DD405BC2-D673-44F0-8833-5CB2A1C186C7'
BINDING = 'D91D429C-1BB5-4640-B49F-69AF14F463E9'
PARAMETER = '7A6A3D31-BE74-4E19-9115-20642944C2E4'
PROXY = '2CA5A1CD-C99B-4C9B-91AF-57989148E841'
LOCATIONS = {0: 'Side1', 1: 'Center', 2: 'Side2'}
SCOPE = 'Observed solid NewBody distance Thin Extrude one/two extent sides, wall enum and owned thickness parameters, using unchanged shared common extrusion controls; closed sketch profiles and one open SketchLine provenance only, no geometry regeneration'


class ThinExtrudeError(ValueError):
    """A framed native True thin flag was seen; preserve its later failure."""


def inspect_thin_extrude(data, records, body, feature, *, features=()):
    """Decode framed block, including ordinaryFalse control; no feature mutation."""
    primary = {}
    for record in records:
        if record.is_primary: primary.setdefault(record.object_id, []).append(record)
    def typed(identity, guid):
        rows = primary.get(identity, [])
        if len(rows) != 1 or rows[0].class_guid != guid:
            raise ValueError('Thin Extrude typed reference missing, ambiguous or wrong class')
        record = rows[0]; return record, data[record.body:record.end]
    feature_record, native = typed(feature['object_id'], EXTRUDE)
    if body != native or feature_record.start != feature['record_offset']:
        raise ValueError('Thin Extrude feature payload/record identity disagrees')
    layout = []
    common, reasons = decode_extrude(body, feature, layout_observer=layout.append)
    if len(layout) != 1: raise ValueError('Shared extrusion layout observer did not provide one bound')
    cursor = start = layout[0]['common_controls_end_offset']
    if body[cursor:cursor+4] != bytes(4): raise ValueError('Unobserved pre-thin extrusion separator')
    cursor += 4
    if cursor >= len(body) or body[cursor] not in (0, 1): raise ValueError('Unobserved native thin-extrude boolean')
    flag_offset = cursor; is_thin = bool(body[cursor]); cursor += 1
    try:
        sides = []
        for side in (1, 2):
            code = struct.unpack_from('<I', body, cursor)[0]; code_offset = cursor; cursor += 4
            binding, after = optional_reference(body, cursor)
            sides.append({'stored_location_code': code, 'location_code_offset': code_offset,
                          'binding_object_id': binding, 'binding_reference_offset': cursor})
            cursor = after
        block_end = cursor
        if not is_thin:
            if any(s['stored_location_code'] != 0 or s['binding_object_id'] is not None for s in sides):
                raise ValueError('Unobserved ordinary extrude inactive wall controls')
            return {'feature_object_id': feature['object_id'], 'is_thin_extrude': False,
                    'stored_flag_offset': flag_offset, 'block_start_offset': start, 'block_end_offset': block_end,
                    'block_hex': body[start:block_end].hex(), 'common_extrusion_controls': common,
                    'scope': 'ObservedFalse flag and absent inactive bindings; ordinary runtime output stays with existing parser'}
        extent = common['extent']; has_two = extent['mode'] == 'TwoSided'
        if (reasons or common['operation']['kind'] != 'NewBody' or common['start'] != {'stored_code': 0, 'kind': 'ProfilePlane'}
                or extent['mode'] not in ('OneSided','TwoSided') or extent['side_one']['condition'] != 'Distance'
                or not math.isfinite(extent['side_one']['distance_cm']) or extent['side_one']['distance_cm'] <= 0
                or extent['side_one'].get('taper_angle_radians') != 0
                or (has_two and (extent['side_two']['condition'] != 'Distance' or extent['side_two']['distance_cm'] <= 0
                                 or extent['side_two'].get('taper_angle_radians') != 0))):
            raise ValueError('Only observed solid NewBody untapered distance Thin Extrude family supported')
        bindings = {p['binding_object_id']:p for p in feature['parameters']}
        def thickness(side):
            info = sides[side-1]; role = 'Side'+str(side)+'WallThickness'; parameter = bindings.get(info['binding_object_id'])
            if parameter is None or parameter['role'] != role or info['stored_location_code'] not in LOCATIONS:
                raise ValueError('Thin Extrude wall location/thickness role unresolved')
            _, binding = typed(info['binding_object_id'], BINDING)
            record, _ = typed(parameter['parameter_object_id'], PARAMETER)
            parsed, rejected = decode_stream(data, [record])
            if len(parsed) != 1 or rejected: raise ValueError('Thin Extrude numeric wall parameter did not revalidate')
            stored = parsed[0]
            if (stored['role'] != role or stored['declared_binding_object_id'] != info['binding_object_id']
                    or stored['raw_float64'] != parameter['raw_float64'] or stored['internal_units'] != 'cm'
                    or not math.isfinite(stored['raw_float64']) or stored['raw_float64'] <= 0
                    or len(binding) != 85 or binding[:5] != b'\1\1\0\0\0'
                    or reference(binding, 5) != feature['object_id'] or reference(binding, 74) != feature['object_id']
                    or reference(binding, 29) != record.object_id
                    or binding[21:29] != data[stored['value_offset']:stored['value_offset']+8]):
                raise ValueError('Thin Extrude wall binding owner/parameter/value copies disagree')
            return {'stored_wall_location_code':info['stored_location_code'],'wall_location':LOCATIONS[info['stored_location_code']],
                    'binding_object_id':info['binding_object_id'],'parameter_object_id':record.object_id,
                    'parameter_role':role,'parameter_name':stored['parameter_name'],
                    'thickness_cm':stored['raw_float64'],'display_units':stored['display_units'],
                    'location_code_offset':info['location_code_offset'],'binding_reference_offset':info['binding_reference_offset']}
        one = thickness(1)
        if has_two:
            two = {'applicable':True, **thickness(2)}
        else:
            if sides[1]['binding_object_id'] is not None or sides[1]['stored_location_code'] != 0:
                raise ValueError('One-sided Thin Extrude inactive second wall frame disagrees')
            two = {'applicable':False,'stored_inactive_location_code':sides[1]['stored_location_code'],
                   'binding_object_id':None,'scope':'Inactive second wall has no actual getter comparison; no active Side1 semantic assigned'}
        # This following profile/body list is independently framed; offsets follow
        # the variable-length optional binding fields, rather than fixed positions.
        if struct.unpack_from('<I',body,cursor)[0] != 1: raise ValueError('Thin Extrude requires one captured profile selection')
        proxy_id = reference(body,cursor+4); cursor += 15
        if body[cursor:cursor+4] != bytes(4) or struct.unpack_from('<I',body,cursor+4)[0] != 1:
            raise ValueError('Thin Extrude output-anchor count/separator unsupported')
        anchor_id = reference(body,cursor+8); _, _ = typed(anchor_id,ANCHOR)
        proxy_record, proxy = typed(proxy_id,PROXY)
        descriptors, properties = native_proxy_references(data,proxy_record)
        if properties or len(descriptors) != 1 or reference(proxy,len(proxy)-11) != feature['object_id']:
            raise ValueError('Thin Extrude profile proxy count/owner unsupported')
        descriptor_rows = primary.get(descriptors[0],[])
        if len(descriptor_rows) != 1: raise ValueError('Thin Extrude profile descriptor ambiguous')
        if descriptor_rows[0].class_guid == '4BD53E5A-0B3E-45E5-AE8B-02044306485A':
            selected = resolve_sketch_profiles(data,records,proxy_id,feature['object_id'],features=features)
            if len(selected) != 1: raise ValueError('Only one captured closed profile supported')
            profile = {'kind':'SketchProfile',**selected[0]}
        elif descriptor_rows[0].class_guid == '5A1BF548-241F-46FD-9FB5-E4B05126EB9D':
            profile = {'profile_kind':'SketchOpenProfile',**resolve_single_sketch_curve(data,records,proxy_id,feature['object_id'],
                features=features,allowed_kinds=('Line',))}
        else: raise ValueError('Unobserved Thin Extrude profile kind')
        anchors = [a for a in decode_body_selections(data,records)['body_anchors'] if a['object_id'] == anchor_id and a['source_owner_object_id'] == feature['object_id']]
        if len(anchors) != 1: raise ValueError('Thin Extrude output anchor is not owned by feature')
        return {'feature_object_id':feature['object_id'],'is_thin_extrude':True,
                'thin_metadata':{'is_thin_extrude':True,'side_one':one,'side_two':two,
                    'wall_side_scope':'One/two extrusion extent sides, not asymmetric offsets about a single profile',
                    'stored_flag_offset':flag_offset,'block_start_offset':start,'block_end_offset':block_end,
                    'block_hex':body[start:block_end].hex(),
                    'offset_scope':'Thin block/location/binding-reference offsets are relative to the native Extrude feature body'},
                'common_extrusion_controls':common,'profile':profile,'profile_proxy_object_id':proxy_id,
                'result_anchor_object_id':anchor_id,'native_body_object_id':anchors[0]['native_body_object_id'],
                'body_scope':'Explicit owned native BODY anchor; current/final lifecycle and exact topology unresolved',
                'geometry_status':'Thin wall controls and source/profile provenance only; no wall geometry regeneration',
                'scope':SCOPE}
    except (ValueError, KeyError, IndexError, TypeError, UnicodeError, struct.error) as error:
        if is_thin: raise ThinExtrudeError(str(error)) from error
        raise


def decode_thin_extrudes(data, records, features):
    """AdditionalTrue-only summary; ordinary/surface features remain unchanged."""
    decoded, unresolved = [], []
    for feature in features:
        if feature['kind']!='Extrude' or feature.get('class_guid')!=EXTRUDE: continue
        choices=[r for r in records if r.is_primary and r.object_id==feature['object_id']]
        if len(choices)!=1:continue
        record=choices[0]
        try:
            row=inspect_thin_extrude(data,records,data[record.body:record.end],feature,features=features)
            if row['is_thin_extrude']:decoded.append(row)
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
            if isinstance(error,ThinExtrudeError) or any(p['role'] in ('Side1WallThickness','Side2WallThickness') for p in feature['parameters']):
                unresolved.append({'feature_object_id':feature['object_id'],'reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,'scope':SCOPE}
