"""Initial BODY-owned FPM provenance with exhaustive BODY-kind naming scope.

This does not relax the trailing edge reader or incomplete global tag audit.
Independent body handles, typed owned selections and body naming must agree;
unknown face tags stay unresolved and literals do not become typed references.
"""
import struct

from asm_records import inspect_asm
from decode_asm_history import decode_asm_history
from decode_asm_recipe_tags import decode_asm_generic_tags, _terms_key
from decode_body_asm_identifiers import MAPPING, _body_identifiers
from decode_body_properties import BODY, COLLECTION
from decode_body_selections import decode_body_selections
from decode_direct_body_features import decode_direct_body_features
from decode_fpm_tracking import DEFINITION, encode_fpm_attribute, _journal_mentions
from decode_parameters import read_string
from decode_recipe_components import decode_counted_recipe
from decode_sketch import reference

SCOPE = ('Initial BODY-owned FPM tracking with same-asset typed handle mapping, reciprocal BoundaryFill-owned '
         'RemoveBody selections and complete initial BODY-kind naming correspondence. Global face naming, '
         'exact selected-source semantics and current/final lifecycle remain unqualified.')


def _int(token, kind):
    value = token['value']
    if token['kind'] != kind or not isinstance(value, int) or isinstance(value, bool):
        raise ValueError('Partial FPM typed integer/pointer invalid')
    return value


def decode_fpm_partial_coverage(data, records, member, members, body_identifier_summary):
    """Return associations/coverage/unresolved and exact handled attribute IDs.

    Separate late native/ASM summary. Existing edge tracking and global generic
    diagnostics retain their scope. Call after explicit body identifier recovery.
    """
    out = {'associations': [], 'coverage': [], 'unresolved': [], 'scope': SCOPE}
    primary_groups = {}
    for record in records:
        if record.is_primary:
            primary_groups.setdefault(record.object_id, []).append(record)
    primary = {i: rows[0] for i, rows in primary_groups.items() if len(rows) == 1}

    def typed(identity, kind):
        rec = primary.get(identity)
        if rec is None or rec.class_guid != kind:
            raise ValueError('Partial FPM native typed reference missing/ambiguous or wrong class')
        return rec, data[rec.body:rec.end]

    for mapping in body_identifier_summary.get('decoded', []):
        try:
            blob_member = mapping['history_blob_member']
            if blob_member not in members:
                raise ValueError('Partial FPM mapped history blob missing')
            blob = members[blob_member]
            parsed = inspect_asm(blob)
            initial = [r for r in parsed['records'] if r['record_kind'] == 'entity' and r['section'] == 'geometry']
            by = {r['index']: r for r in initial}
            targets = [r for r in parsed['records'] if r['name'] == 'ATTRIB_CUSTOM-attrib'
                       and len(r['tokens']) > 5 and r['tokens'][5]['kind'] == 'string' and r['tokens'][5]['value'] == DEFINITION]
            body_targets = [r for r in targets if r['index'] in by and len(r['tokens']) > 4
                            and r['tokens'][4]['kind'] == 'pointer'
                            and by.get(r['tokens'][4]['value'], {}).get('name') == 'body']
            if not body_targets:
                continue
            if (member not in members or members[member] != data
                    or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat')
                    or member.count('/FusionDesignSegmentType1/') != 1 or not parsed['complete_token_stream']):
                raise ValueError('Partial FPM same-asset Design bytes or complete ASM scope disagrees')
            _, payload = typed(mapping['mapping_record_object_id'], MAPPING)
            if payload[:2] != bytes(2) or len(payload) < 6:
                raise ValueError('Partial FPM mapping header unsupported')
            count = struct.unpack_from('<I', payload, 2)[0]
            cursor = 6+16*count
            if not 1 <= count <= 1024 or cursor+16 > len(payload):
                raise ValueError('Partial FPM mapping count/extent invalid')
            pairs = [struct.unpack_from('<QQ', payload, 6+16*i) for i in range(count)]
            if (len({h for h, _ in pairs}) != count or len({b for _, b in pairs}) != count
                    or pairs != [(b['stored_handle'], b['native_body_object_id']) for b in mapping['bindings']]
                    or mapping['body_count'] != count):
                raise ValueError('Partial FPM mapping handle/body table is not the supplied bijection')
            collection = reference(payload, cursor)
            typed(collection, COLLECTION)
            filename, end = read_string(payload, cursor+12)
            expected = member.rsplit('/FusionDesignSegmentType1/', 1)[0]+'/Breps.BlobParts/'+filename
            if (collection != mapping['owner_object_id'] or payload[cursor+11] != 0 or end != len(payload)
                    or not filename.startswith('BREP.') or not filename.endswith('.smbh')
                    or '/' in filename or '\\' in filename or expected != blob_member):
                raise ValueError('Partial FPM explicit same-asset mapping owner/filename disagrees')
            roots, _, _ = _body_identifiers(parsed, blob)
            if set(roots) != {h for h, _ in pairs}:
                raise ValueError('Partial FPM typed BODY stored handles differ from native mapping')
            for binding in mapping['bindings']:
                _, body = typed(binding['native_body_object_id'], BODY)
                if (reference(body, len(body)-11) != collection
                        or roots[binding['stored_handle']]['index'] != binding['asm_body_index']):
                    raise ValueError('Partial FPM retained native collection or typed initial BODY association disagrees')
            bindings = {b['asm_body_index']: b for b in mapping['bindings']}
            history = decode_asm_history(blob, parsed=parsed)
            ordinals = {r['inspection_record_index']: r['geometry_entity_ordinal'] for r in history['geometry_entities']}

            def ptr(rec, field, nullable=False):
                value = _int(rec['tokens'][field], 'pointer')
                if nullable and value == -1:
                    return None
                if value not in by:
                    raise ValueError('Partial FPM pointer leaves bounded initial geometry')
                return value

            attributes = []
            for rec in body_targets:
                ts = rec['tokens']
                if (len(ts) != 8 or [t['tag'] for t in ts] != [12,4,12,12,12,7,4,4]
                        or _int(ts[0], 'pointer') != -1 or _int(ts[1], 'integer') != -1
                        or _int(ts[6], 'integer') != 1 or not 1 <= _int(ts[7], 'integer') <= 0xffffffff):
                    raise ValueError('Partial FPM initial BODY attribute framing unsupported')
                owner = ptr(rec, 4)
                if owner not in bindings or by[owner]['name'] != 'body':
                    raise ValueError('Partial FPM owner is not an explicitly mapped initial BODY')
                current, previous, chain = ptr(by[owner], 0, True), None, []
                while current is not None:
                    if current in chain or len(chain) >= 128:
                        raise ValueError('Partial FPM BODY attribute chain cyclic/oversized')
                    attr = by[current]
                    ats = attr['tokens']
                    if (attr['name'] != 'ATTRIB_CUSTOM-attrib' or len(ats) < 6
                            or [t['tag'] for t in ats[:5]] != [12,4,12,12,12]
                            or _int(ats[0], 'pointer') != -1 or _int(ats[1], 'integer') != -1
                            or ptr(attr, 4) != owner or ptr(attr, 3, True) != previous):
                        raise ValueError('Partial FPM BODY/attribute chain is not reciprocal')
                    chain.append(current)
                    previous, current = current, ptr(attr, 2, True)
                if rec['index'] not in chain:
                    raise ValueError('Partial FPM attribute absent from owner chain')
                item = {'attribute_record_index': rec['index'], 'attribute_geometry_ordinal': ordinals[rec['index']],
                    'section': 'geometry', 'definition_name': DEFINITION, 'stored_tracking_literal': ts[7]['value'],
                    'stored_schema_integer': 1, 'stored_token_fields': [[t['tag'],t['value']] for t in ts],
                    'owner_kind': 'body', 'owner_body_record_index': owner, 'owner_body_geometry_ordinal': ordinals[owner],
                    'owner_attribute_chain_record_indices': chain, 'payload_offset': ts[0]['offset'],
                    'payload_end_offset': rec['end_offset']-1, 'payload_hex': blob[ts[0]['offset']:rec['end_offset']-1].hex(),
                    'attribute_journal_mentions': _journal_mentions(history, ordinals[rec['index']]),
                    'owner_journal_mentions': _journal_mentions(history, ordinals[owner])}
                if encode_fpm_attribute(item).hex() != item['payload_hex']:
                    raise ValueError('Partial FPM exact original attribute payload replay disagrees')
                attributes.append(item)
            # Inventory all initial custom owners before restricting uniqueness to
            # BODY-kind tags. An untyped owner cannot silently be excluded.
            for rec in initial:
                if rec['name'] == 'ATTRIB_CUSTOM-attrib':
                    ptr(rec, 4)
            tags = decode_asm_generic_tags(blob, parsed=parsed, allow_fpm_tracking=True)
            handled = {a['attribute_record_index'] for a in attributes}
            remaining = [u for u in tags['unresolved'] if u['attribute_record_index'] not in handled]
            if any(by[ptr(by[u['attribute_record_index']], 4)]['name'] == 'body' for u in remaining):
                raise ValueError('Incomplete initial BODY-kind naming coverage')
            body_tags = [t for t in tags['tags'] if t['owner_kind'] == 'body']
            if (len(body_tags) != len(roots) or {t['owner_record_index'] for t in body_tags} != set(bindings)):
                raise ValueError('Initial BODY naming is not exactly one validated tag per mapped root')
            coverage = {'mapping_record_object_id': mapping['mapping_record_object_id'], 'history_blob_member': blob_member,
                'initial_BODY_record_indices': sorted(bindings), 'validated_initial_BODY_generic_tags': body_tags,
                'handled_initial_BODY_FPM_attribute_record_indices': sorted(handled), 'initial_BODY_naming_complete': True,
                'global_generic_tag_coverage_complete': not remaining,
                'remaining_other_kind_generic_tag_failures': [dict(u, owner_kind=by[ptr(by[u['attribute_record_index']], 4)]['name']) for u in remaining],
                'scope': 'Exhaustive initial BODY-kind namespace only. Face/edge/global naming failures are retained; no global uniqueness claim.'}
            out['coverage'].append(coverage)
            selections = decode_body_selections(data, records)
            direct = decode_direct_body_features(data, records, selections)
            for attr in attributes:
                try:
                    literal = attr['stored_tracking_literal']
                    duplicates = [r for r in targets if len(r['tokens']) == 8 and r['tokens'][7]['kind'] == 'integer' and r['tokens'][7]['value'] == literal]
                    if len(duplicates) != 1 or any(len(r['tokens']) != 8 or r['tokens'][7]['kind'] != 'integer' for r in targets):
                        raise ValueError('Partial FPM literal uniqueness is ambiguous or unframed')
                    actions = [a for a in direct['decoded'] if a['kind'] == 'RemoveBody' and a['descriptor_object_id'] == literal]
                    if len(actions) != 1:
                        raise ValueError('Partial FPM literal lacks one independently validated BoundaryFill removal action')
                    action = actions[0]
                    binding = bindings[attr['owner_body_record_index']]
                    if action['native_body_object_id'] != binding['native_body_object_id']:
                        raise ValueError('Partial FPM owner BODY mapping disagrees with independently typed removal selection')
                    descriptor = next(d for d in selections['body_descriptors'] if d['object_id'] == literal)
                    parent_proxy = next(p for p in selections['selection_proxies'] if p['selection_record_object_id'] == action['matching_parent_tool_selection_record_object_id'])
                    parent_descriptor, = [d for d in selections['body_descriptors'] if d['object_id'] in parent_proxy['descriptor_object_ids']]
                    recipes = []
                    for desc in (descriptor, parent_descriptor):
                        recipe_rec = primary.get(desc['recipe_record_object_id'])
                        if recipe_rec is None:
                            raise ValueError('Partial FPM body recipe missing/ambiguous')
                        recipe = decode_counted_recipe(data, recipe_rec)
                        if (recipe['payload_kind'] != 'body_recipe_data' or recipe['payload_hex'] != '00000000ffffffff'
                                or len(recipe['name_table']) != 1 or recipe['name_table'][0]['table_index'] != 0):
                            raise ValueError('Unobserved partial FPM body-recipe layout')
                        recipes.append(recipe)
                    if recipes[0]['name_table'] != recipes[1]['name_table']:
                        raise ValueError('Removal and parent-tool naming tuples differ')
                    matches = [t for t in body_tags if _terms_key(t['terms']) == _terms_key(recipes[0]['name_table'][0]['terms'])]
                    if len(matches) != 1 or matches[0]['owner_record_index'] != attr['owner_body_record_index']:
                        raise ValueError('Unique BODY-kind recipe naming does not agree with FPM owner and native mapping')
                    out['associations'].append({'stored_tracking_literal': literal, 'FPM_attribute': attr,
                        'mapping_record_object_id': mapping['mapping_record_object_id'], 'history_blob_member': blob_member,
                        'feature_object_id': action['feature_object_id'], 'parent_boundary_fill_object_id': action['parent_boundary_fill_object_id'],
                        'owned_removal_action': action, 'native_body_object_id': binding['native_body_object_id'],
                        'same_asset_mapping': {'mapping_record_object_id': mapping['mapping_record_object_id'],
                            'collection_object_id': collection, 'history_blob_member': blob_member,
                            'stored_native_handle': binding['stored_handle'], 'initial_ASM_BODY_record_index': binding['asm_body_index']},
                        'removal_body_descriptor': descriptor, 'parent_tool_body_descriptor': parent_descriptor,
                        'removal_and_parent_tool_recipes': recipes, 'unique_initial_BODY_naming_correspondence': matches[0],
                        'correspondence_status': 'InitialBODYFPMOwnerMatchesExplicitMappedRemovalBodyAndBODYScopedRecipeNaming',
                        'literal_is_serialized_native_reference': False, 'exact_selected_source_identity': None,
                        'qualified_historical_state': None, 'source_curve_geometry': None, 'scope': SCOPE})
                except (ValueError, KeyError, IndexError, StopIteration, struct.error) as error:
                    out['unresolved'].append({'history_blob_member': blob_member, 'attribute_record_index': attr['attribute_record_index'], 'reason': str(error)})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            out['unresolved'].append({'mapping_record_object_id': mapping.get('mapping_record_object_id'), 'reason': str(error)})
    return out
