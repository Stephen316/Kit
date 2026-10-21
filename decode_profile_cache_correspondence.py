"""Qualified Extrude-profile to stored COEDGE tag correspondences.

This is source-profile/cache provenance, not a global interpretation of sketch
attribute numbers. All matching coedges are retained. Cached geometry may be
modified after the source Extrude and is never used to choose an association.
"""
import struct
import uuid

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections
from decode_brep import decode_topology
from decode_extrude import decode_extrude
from decode_parameters import read_string
from decode_profiles import PROFILE_DESCRIPTOR_GUID, PROFILE_LOOP_GUID, read_loops
from decode_sketch import attributes, reference
from decode_sketch_attributes import decode_sketch_attribute

EXTRUDE = 'DD405BC2-D673-44F0-8833-5CB2A1C186C7'
SKETCH = '44A64366-4BD3-4B24-881A-F94C206E8F2D'
CURVES = {'Line': 'DCA267ED-D615-4934-B64F-AD805E8003E2',
          'Circle': 'F0130424-8B7E-4092-93C9-1CA807482534'}
SCOPE = 'Observed NewBody Extrude owned profile/native sketch curve tags and explicit source-owner BODY/blob route qualify multiple matching COEDGE sketch-attribute first-field correspondences; geometry, other fields and lifecycle not inferred'


def decode_profile_cache_correspondence(data, records, features, member, members, body_identifier_summary):
    """Separate decoded/unresolved/scope; do not clear previous selection warnings."""
    grouped = {}
    for r in records:
        if r.is_primary: grouped.setdefault(r.object_id, []).append(r)
    primary = {identity: rows[0] for identity, rows in grouped.items() if len(rows) == 1}
    def typed(identity, guid):
        r = primary.get(identity)
        if r is None or r.class_guid != guid:
            raise ValueError('Profile-cache typed reference missing, ambiguous or wrong class')
        return r, data[r.body:r.end]
    anchors = decode_body_selections(data, records)['body_anchors']
    verified = decode_body_asm_identifiers(data, records, member, members, {'decoded': body_identifier_summary['decoded']})
    decoded, unresolved = [], []
    for feature in features:
        if feature['kind'] != 'Extrude': continue
        owner = feature['object_id']
        source_anchors = [a for a in anchors if a['source_owner_object_id'] == owner]
        if not source_anchors: continue
        try:
            if len(source_anchors) != 1:
                raise ValueError('Only observed single-source-BODY Extrude anchor family supported')
            _, source = typed(owner, EXTRUDE)
            settings, reasons = decode_extrude(source, feature)
            if settings['operation']['kind'] != 'NewBody':
                raise ValueError('Only observed NewBody Extrude profile-cache family supported')
            descriptors = []
            for r in primary.values():
                if r.class_guid == PROFILE_DESCRIPTOR_GUID:
                    body = data[r.body:r.end]
                    if len(body) >= 17 and reference(body, len(body)-11) == owner: descriptors.append((r, body))
            if len(descriptors) != 1:
                raise ValueError('Profile-cache requires one explicitly owned profile descriptor')
            descriptor, body = descriptors[0]
            if body[:2] != bytes(2) or struct.unpack_from('<I', body, 13)[0] != 1:
                raise ValueError('Unsupported profile-cache descriptor count/prefix')
            namespace, cursor = read_string(body, 17); sketch_text, cursor = read_string(body, cursor)
            if len(namespace) != 36 or not sketch_text.isascii() or not sketch_text.isdecimal():
                raise ValueError('Profile-cache descriptor sketch namespace not explicit')
            uuid.UUID(namespace); sketch_id = int(sketch_text); typed(sketch_id, SKETCH)
            sketches = [s for s in features if s['kind'] == 'Sketch' and s['sketch_object_id'] == sketch_id]
            if len(sketches) != 1: raise ValueError('Profile-cache native Sketch unresolved or ambiguous')
            sketch = sketches[0]
            definition_id = reference(body, 2); _, definition = typed(definition_id, PROFILE_LOOP_GUID)
            loops = read_loops(definition, descriptor.object_id, sketch)
            references = [r for loop in loops for r in loop['curve_references']]
            sources = {}
            for ref in references:
                if ref['entity_kind'] not in CURVES:
                    raise ValueError('Only observed Line/Circle profile-cache sources supported')
                _, native = typed(ref['entity_id'], CURVES[ref['entity_kind']])
                if native[:2] != b'\0\1' or reference(native, len(native)-11) != sketch_id:
                    raise ValueError('Profile-cache native curve does not belong to explicit Sketch')
                props, _ = attributes(native, 2)
                if props.get('crv_primary_id') != ref['entity_tag'] or props.get('crv_secondary_id') != 0:
                    raise ValueError('Profile-cache native primary/secondary curve tag disagrees')
                if ref['entity_tag'] in sources and sources[ref['entity_tag']]['native_entity_object_id'] != ref['entity_id']:
                    raise ValueError('Ambiguous native profile curve tag')
                sources[ref['entity_tag']] = {'native_entity_object_id': ref['entity_id'], 'native_entity_kind': ref['entity_kind'],
                    'native_entity_tag': ref['entity_tag'], 'tag_property': 'crv_primary_id', 'cached_coedge_candidates': []}
            if not sources: raise ValueError('Empty profile-cache source curve set')
            for anchor in source_anchors:
                mappings = [(m,b) for m in verified['decoded'] for b in m['bindings'] if b['native_body_object_id'] == anchor['native_body_object_id']]
                if len(mappings) != 1: raise ValueError('Profile-cache source BODY lacks explicit same-asset stored-ID mapping')
                mapping,binding = mappings[0]; blob_member=mapping['history_blob_member']; blob=members[blob_member]
                parsed=inspect_asm(blob); summary=decode_asm_generic_tags(blob,parsed,allow_fpm_tracking=True)
                if summary['unresolved']: raise ValueError('Profile-cache initial attribute framing incomplete')
                topology=decode_topology(parsed)
                if topology['unresolved']: raise ValueError('Profile-cache initial typed topology incomplete')
                nodes={n['index']:n for n in topology['nodes']}
                graphs=[g for g in topology['body_graphs'] if g['body_index']==binding['asm_body_index']]
                if len(graphs)!=1: raise ValueError('Profile-cache mapped BODY graph missing or ambiguous')
                graph=graphs[0]; matched={tag:{**row,'cached_coedge_candidates':[]} for tag,row in sources.items()}
                for item in summary['ignored_validated_other_definition_attributes']:
                    if item['definition_name']!='sketch_attrib_def' or item['owner_kind']!='coedge' or item['owner_record_index'] not in graph['coedge_indices']:continue
                    record=parsed['records'][item['attribute_record_index']]; payload=decode_sketch_attribute(record)
                    fields=payload['stored_decimal_text_fields']; possible=[tag for tag in sources if str(tag)==fields[0]]
                    if fields[1:]!=['0','0','0','1','1'] or len(possible)!=1:
                        raise ValueError('Mapped BODY COEDGE sketch text outside complete owned-profile tag family')
                    tag=possible[0]; coedge=nodes[item['owner_record_index']]; edge=nodes[coedge['edge_index']]
                    loop=nodes[coedge['loop_index']]; face=nodes[loop['face_index']]
                    if (loop['index'] not in graph['loop_indices'] or face['index'] not in graph['face_indices'] or edge['index'] not in graph['edge_indices']
                            or nodes[coedge['next_coedge_index']]['previous_coedge_index']!=coedge['index']
                            or nodes[coedge['previous_coedge_index']]['next_coedge_index']!=coedge['index']):
                        raise ValueError('Profile-cache COEDGE/edge/loop/face ownership not reciprocal')
                    matched[tag]['cached_coedge_candidates'].append({'attribute_record_index':record['index'],
                        'uninterpreted_text':payload['uninterpreted_text'],'stored_decimal_text_fields':fields,
                        'coedge_record_index':coedge['index'],'edge_record_index':edge['index'],'loop_record_index':loop['index'],
                        'face_record_index':face['index'],'curve_record_index':edge['curve_index'],
                        'curve_kind':nodes[edge['curve_index']]['kind'],
                        'endpoint_vertex_record_indices':[edge['start_vertex_index'],edge['end_vertex_index']]})
                if any(not row['cached_coedge_candidates'] for row in matched.values()):
                    raise ValueError('Owned profile curve set lacks complete mapped COEDGE correspondence')
                decoded.append({'source_feature_object_id':owner,'feature_object_id':owner,'source_feature_kind':'Extrude',
                    'profile_descriptor_object_id':descriptor.object_id,'profile_loop_definition_object_id':definition_id,
                    'native_sketch_object_id':sketch_id,'source_sketch_feature_object_id':sketch['object_id'],
                    'native_sketch_name':sketch.get('name'),'namespace_text':namespace,'profile_loops':loops,
                    'body_anchor_object_id':anchor['object_id'],'native_body_object_id':anchor['native_body_object_id'],
                    'mapping_record_object_id':mapping['mapping_record_object_id'],'history_blob_member':blob_member,
                    'asm_body_index':graph['body_index'],'asm_stored_body_entity_id':binding['stored_handle'],
                    'source_curves':[matched[tag] for tag in sorted(matched)],
                    'comparison_basis':'Canonical decimal first text field equals crv_primary_id only after explicit owned native profile/Sketch/entity and source-owner BODY/blob routes; all matching COEDGE candidates retained',
                    'identity_status':'Qualified multiple profile-cache naming correspondence, not universal ID conversion or uniquely selected geometry',
                    'geometry_status':'Geometry not used to select candidates; transformed/modified cache may differ from original sketch',
                    'remaining_uncertainty':['Other five text fields remain literal strings','Unbound .smb EDGE/VERTEX attributes not converted to native entity tags','Historical/current/final lifecycle and persistent topology identity','General feature regeneration and parameterization']})
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
            unresolved.append({'source_feature_object_id':owner,'reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,'scope':SCOPE}
