"""Exact initial-geometry ASM generic tags and native recipe naming candidates.

Shared names/index/component tuples establish serialized naming correspondence,
not a universal persistent topology identity. All matching owners are retained;
duplicate tags, including detached copies, never resolve a selected source.
"""
import struct

from asm_records import inspect_asm
from decode_body_asm_identifiers import MAPPING, _body_identifiers
from decode_body_properties import BODY, COLLECTION
from decode_brep import decode_topology
from decode_parameters import read_string
from decode_pipe_edge_controls import inspect_pipe_edge_controls
from decode_recipe_components import decode_counted_recipe
from decode_sketch import reference

DEFINITION = 'generic_tag_attrib_def'
SCOPE = 'Observed exact ASM generic-tag counted term grammar and native recipe name/index/component correspondence in the explicitly mapped same-asset blob; ambiguous cache owners retained without persistent topology/source closure claims'


def _integer(token, low, high):
    value = token['value']
    if token['kind'] != 'integer' or not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
        raise ValueError('ASM generic tag integer kind/range mismatch')
    return value


def _ascii(token):
    value = token['value']
    if token['kind'] != 'string' or not isinstance(value, str) or not 1 <= len(value) <= 128:
        raise ValueError('ASM generic tag string kind/extent mismatch')
    if any(ord(char) < 32 or ord(char) > 126 for char in value):
        raise ValueError('ASM generic tag requires observed printable ASCII strings')
    return value


def encode_generic_tag_payload(tag):
    """Replay typed payload from definition name through the last zero terminator."""
    def integer(value):
        return b'\x04'+struct.pack('<q', value)

    def text(value):
        raw = value.encode('ascii')
        if len(raw) > 255:
            raise ValueError('ASM generic tag short string exceeds255 bytes')
        return b'\x07'+bytes([len(raw)])+raw

    output = text(tag['definition_name'])
    for value in tag['stored_definition_schema_fields']:
        output += integer(value)
    output += text(tag['stored_namespace_text'])+integer(len(tag['terms']))
    for term in tag['terms']:
        output += integer(len(term['name'].encode('ascii')))+text(term['name'])+integer(term['stored_index'])
        components = term['stored_reference_components_int32']
        output += integer(len(components))
        for value in components:
            output += integer(value)
        output += integer(0)
    return output


def decode_asm_generic_tags(blob, parsed=None):
    """Return framed tags/unresolved/scope; only initial geometry is examined."""
    parsed = parsed if parsed is not None else inspect_asm(blob)
    if not parsed['complete_token_stream']:
        raise ValueError('Generic tags require a complete bounded ASM token stream')
    records = parsed['records']
    limit = next((r['index'] for r in records if r['record_kind'] == 'marker'), len(records))

    def pointer(token, nullable=False):
        value = token['value']
        if token['kind'] != 'pointer' or not isinstance(value, int) or isinstance(value, bool):
            raise ValueError('ASM generic tag association lacks typed pointer')
        if nullable and value == -1:
            return None
        if not 0 <= value < limit:
            raise ValueError('ASM generic tag pointer leaves initial geometry')
        return value

    def attribute_header(record, owner):
        tokens = record['tokens']
        if record['name'] != 'ATTRIB_CUSTOM-attrib' or len(tokens) < 6:
            raise ValueError('Unobserved generic-tag attribute chain class/header')
        if (pointer(tokens[0], True) is not None or _integer(tokens[1], -1, -1) != -1
                or pointer(tokens[4]) != owner):
            raise ValueError('ASM attribute owner/header correspondence disagrees')
        return pointer(tokens[2], True), pointer(tokens[3], True)

    def owner_chain(owner_id, target_attribute, allowed_kinds=('body', 'face', 'edge')):
        owner = records[owner_id]
        if owner['name'] not in allowed_kinds or len(owner['tokens']) < 1:
            raise ValueError('Custom attribute owner is not an observed typed owner for this definition')
        current = pointer(owner['tokens'][0], True)
        previous, chain = None, []
        while current is not None:
            if current in chain or len(chain) >= 128:
                raise ValueError('Cyclic or oversized ASM attribute owner chain')
            chain.append(current)
            following, stored_previous = attribute_header(records[current], owner_id)
            if stored_previous != previous:
                raise ValueError('ASM attribute next/previous owner chain is not reciprocal')
            previous, current = current, following
        if target_attribute not in chain:
            raise ValueError('ASM generic tag is absent from its claimed owner attribute chain')
        return chain

    tags, unresolved, ignored = [], [], []
    for record in records[:limit]:
        tokens = record['tokens']
        if record['name'] != 'ATTRIB_CUSTOM-attrib':
            continue
        try:
            if len(tokens) < 6 or tokens[5]['kind'] != 'string':
                raise ValueError('Unobserved custom attribute definition framing prevents complete generic-tag audit')
            owner_id = pointer(tokens[4])
            definition = _ascii(tokens[5])
            if definition == 'Timestamp_attrib_def':
                owner_chain(owner_id, record['index'], ('body',))
                if (len(tokens) != 8 or _integer(tokens[6], 1, 1) != 1 or tokens[7]['kind'] != 'double'):
                    raise ValueError('Unobserved timestamp definition framing prevents complete generic-tag audit')
                ignored.append({'attribute_record_index': record['index'], 'definition_name': definition,
                                'owner_record_index': owner_id, 'owner_kind': 'body'})
                continue
            if definition == 'sketch_attrib_def':
                owner_chain(owner_id, record['index'], ('coedge',))
                if len(tokens) != 10 or [_integer(t, 1, 3) for t in tokens[6:9]] != [1, 1, 3]:
                    raise ValueError('Unobserved sketch attribute framing prevents complete generic-tag audit')
                sketch_text = _ascii(tokens[9])
                parts = sketch_text.split(' ')
                if len(parts) != 6 or any(not part.isdecimal() for part in parts):
                    raise ValueError('Unobserved sketch attribute opaque text layout prevents complete generic-tag audit')
                ignored.append({'attribute_record_index': record['index'], 'definition_name': definition,
                                'owner_record_index': owner_id, 'owner_kind': 'coedge',
                                'uninterpreted_text': sketch_text})
                continue
            if definition != DEFINITION:
                raise ValueError('Unobserved custom attribute definition prevents complete generic-tag audit')
            chain = owner_chain(owner_id, record['index'])
            schema = [_integer(t, -1, 3) for t in tokens[6:9]]
            namespace = _ascii(tokens[9])
            if schema != [3, 3, -1] or namespace != definition+' ':
                raise ValueError('Unobserved ASM generic-tag definition/schema namespace')
            count = _integer(tokens[10], 1, 2)
            cursor, terms = 11, []
            for _ in range(count):
                size = _integer(tokens[cursor], 1, 128)
                name = _ascii(tokens[cursor+1])
                if len(name.encode('ascii')) != size:
                    raise ValueError('ASM generic-tag explicit name length disagrees')
                stored_index = _integer(tokens[cursor+2], 0, 0xffffffff)
                component_count = _integer(tokens[cursor+3], 0, 1)
                cursor += 4
                components = [_integer(tokens[cursor+i], -0x80000000, 0x7fffffff) for i in range(component_count)]
                cursor += component_count
                if _integer(tokens[cursor], 0, 0) != 0:
                    raise ValueError('ASM generic-tag reference terminator is not zero')
                cursor += 1
                terms.append({'name': name, 'stored_index': stored_index,
                              'stored_reference_component_count': component_count,
                              'stored_reference_components_int32': components,
                              'stored_reference_components_uint32': [value & 0xffffffff for value in components],
                              'stored_reference_terminator_uint32': 0})
            if cursor != len(tokens):
                raise ValueError('Unconsumed ASM generic-tag payload fields')
            start, end = tokens[5]['offset'], record['end_offset']-1
            tag = {'attribute_record_index': record['index'], 'owner_record_index': owner_id,
                   'owner_kind': records[owner_id]['name'], 'owner_attribute_chain': chain,
                   'definition_name': definition, 'stored_definition_schema_fields': schema,
                   'stored_namespace_text': namespace, 'stored_term_count': count, 'terms': terms,
                   'payload_offset': start, 'payload_end_offset': end, 'payload_hex': blob[start:end].hex(),
                   'scope': 'Explicit reciprocal attribute owner and framed serialized naming tuple; design object and persistent topology identity unresolved'}
            if encode_generic_tag_payload(tag) != blob[start:end]:
                raise ValueError('ASM generic-tag exact byte replay disagrees')
            tags.append(tag)
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'attribute_record_index': record['index'], 'reason': str(error)})
    return {'tags': tags, 'ignored_validated_other_definition_attributes': ignored,
            'unresolved': unresolved, 'scope': SCOPE}


def _terms_key(terms):
    result = []
    for term in terms:
        values = term['stored_reference_components_int32']
        if term['stored_reference_component_count'] != len(values) or term['stored_reference_terminator_uint32'] != 0:
            raise ValueError('Counted recipe/tag term framing disagrees')
        result.append((term['name'], term['stored_index'], tuple(values)))
    return tuple(result)


def match_recipe_tag_names(recipe, tag_summary, *, parsed=None):
    """All exact term-group matches, with no selection or ambiguity fallback."""
    if tag_summary['unresolved']:
        raise ValueError('Incomplete initial-geometry generic-tag coverage prevents uniqueness claims')
    indexed = {}
    for tag in tag_summary['tags']:
        indexed.setdefault(_terms_key(tag['terms']), []).append(tag)
    topology = decode_topology(parsed) if parsed is not None else None
    nodes = {n['index']: n for n in topology['nodes']} if topology else {}
    matches = []
    for entry in recipe['name_table']:
        found = indexed.get(_terms_key(entry['terms']), [])
        candidates = []
        for tag in found:
            owner = tag['owner_record_index']
            candidate = {'attribute_record_index': tag['attribute_record_index'],
                         'owner_record_index': owner, 'owner_kind': tag['owner_kind']}
            if topology is not None:
                candidate['body_graph_membership'] = [g['body_index'] for g in topology['body_graphs']
                    if owner == g['body_index'] or owner in g[{'face': 'face_indices', 'edge': 'edge_indices'}.get(tag['owner_kind'], 'edge_indices')]]
                node = nodes.get(owner)
                if node and tag['owner_kind'] == 'edge':
                    curve = nodes.get(node['curve_index'])
                    candidate.update(curve_index=node['curve_index'], curve_kind=curve['kind'] if curve else None,
                                     endpoint_vertex_indices=[node['start_vertex_index'], node['end_vertex_index']],
                                     cached_endpoint_identity_same=node['start_vertex_index'] == node['end_vertex_index'])
            candidates.append(candidate)
        matches.append({'name_table_index': entry['table_index'], 'term_count': len(entry['terms']),
                        'candidate_count': len(candidates), 'candidates': candidates,
                        'status': 'AmbiguousStoredNamingCorrespondence' if len(candidates) > 1 else
                                  'UniqueStoredNamingCorrespondence' if candidates else 'NoStoredNamingCorrespondence',
                        'selected_source_owner_record_index': None,
                        'scope': 'Exact complete stored term-group equality only; native recipe operation payload remains uninterpreted'})
    return {'recipe_object_id': recipe['object_id'], 'payload_kind': recipe['payload_kind'], 'name_entries': matches,
            'selected_source_status': 'Unresolved; per-name tuple correspondence does not decode the whole recipe operation or choose among duplicate cache owners',
            'scope': SCOPE}


def inspect_pipe_recipe_tags(data, records, body, feature, features, member, members, body_identifier_summary, *, source_evidence=None):
    """Native Pipe source/body/blob route and exact naming candidate evidence only."""
    source = source_evidence if source_evidence is not None else inspect_pipe_edge_controls(data, records, body, feature, features)
    native_body_id = source['path']['native_body_object_id']
    mappings = [(mapping, binding) for mapping in body_identifier_summary['decoded'] for binding in mapping['bindings']
                if binding['native_body_object_id'] == native_body_id]
    if len(mappings) != 1:
        raise ValueError('Pipe source native body does not resolve to one explicit ASM mapping')
    mapping, binding = mappings[0]
    primary = {}
    for record in records:
        if record.is_primary:
            primary.setdefault(record.object_id, []).append(record)

    def typed(identity, guid):
        choices = primary.get(identity, [])
        if len(choices) != 1 or choices[0].class_guid != guid:
            raise ValueError('Pipe naming source/blob typed association missing or ambiguous')
        record = choices[0]
        return record, data[record.body:record.end]

    _, payload = typed(mapping['mapping_record_object_id'], MAPPING)
    typed(native_body_id, BODY)
    if payload[:2] != bytes(2):
        raise ValueError('Pipe native body mapping prefix disagrees')
    count = struct.unpack_from('<I', payload, 2)[0]
    cursor = 6+16*count
    if not 1 <= count <= 1024 or cursor+16 > len(payload):
        raise ValueError('Pipe native body mapping count/extent unsupported')
    entries = [struct.unpack_from('<QQ', payload, 6+16*i) for i in range(count)]
    if entries.count((binding['stored_handle'], native_body_id)) != 1:
        raise ValueError('Pipe native body/handle pair disagrees with explicit mapping')
    owner = reference(payload, cursor)
    typed(owner, COLLECTION)
    if mapping['owner_object_id'] != owner or mapping['body_count'] != count:
        raise ValueError('Pipe supplied body mapping owner/count disagrees with stored frame')
    if payload[cursor+11] != 0:
        raise ValueError('Pipe native mapping filename separator disagrees')
    filename, end = read_string(payload, cursor+12)
    if (end != len(payload) or not filename.startswith('BREP.') or not filename.endswith('.smbh')
            or '/' in filename or '\\' in filename):
        raise ValueError('Pipe native mapping filename unsupported')
    blob_member = member.rsplit('/FusionDesignSegmentType1/', 1)[0]+'/Breps.BlobParts/'+filename
    if blob_member != mapping['history_blob_member'] or blob_member not in members:
        raise ValueError('Pipe explicit same-asset history blob association disagrees')
    blob = members[blob_member]
    parsed = inspect_asm(blob)
    roots, _, _ = _body_identifiers(parsed, blob)
    if (set(roots) != {handle for handle, _ in entries}
            or roots[binding['stored_handle']]['index'] != binding['asm_body_index']):
        raise ValueError('Pipe native handle/initial ASM BODY association is not explicit and bijective')
    limit = next((r['index'] for r in parsed['records'] if r['record_kind'] == 'marker'), len(parsed['records']))
    root_index = binding['asm_body_index']
    if not 0 <= root_index < limit:
        raise ValueError('Pipe mapped ASM BODY index leaves initial geometry')
    root = parsed['records'][root_index]
    if (root['name'] != 'body' or root['tokens'][1]['kind'] != 'integer'
            or root['tokens'][1]['value'] != binding['stored_handle']):
        raise ValueError('Pipe native mapping handle/typed ASM BODY stored ID disagrees')
    tag_summary = decode_asm_generic_tags(blob, parsed)
    recipe_record, _ = typed(source['path']['recipe']['object_id'], '7ACC2A03-0261-4879-A14A-A93D661A5BDC')
    recipe = decode_counted_recipe(data, recipe_record)
    correspondence = match_recipe_tag_names(recipe, tag_summary, parsed=parsed)
    return {'feature_object_id': feature['object_id'], 'source_descriptor_object_id': source['path']['descriptor_object_id'],
            'source_recipe_object_id': recipe['object_id'], 'source_body_anchor_object_id': source['path']['body_anchor_object_id'],
            'native_source_body_object_id': native_body_id, 'mapping_record_object_id': mapping['mapping_record_object_id'],
            'history_blob_member': blob_member, 'stored_source_body_handle': binding['stored_handle'],
            'explicit_asm_source_body_index': root_index, 'initial_generic_tag_count': len(tag_summary['tags']),
            'native_descriptor_namespace_text': source['path']['namespace_text'],
            'native_descriptor_entity_guid_text': source['path']['entity_guid_text'],
            'namespace_scope': 'Native descriptor UUID namespace and literal ASM generic-tag namespace retained separately; only explicit same-asset blob scope joins them, not presumed namespace-text equality',
            'recipe_naming_correspondence': correspondence,
            'source_edge_is_closed': None, 'source_curve_geometry': None,
            'tool_settings_status': 'Unresolved; exact stored naming candidates retained without selecting a source edge or closure',
            'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    """Six saved Pipe archives; all initial tags, exact byte replay and guards."""
    import copy
    import json
    from pathlib import Path
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    root = Path(root)
    folder = 'pipeedgecontrasts-5bd287323ae7'
    truth = json.loads((root/folder/'ground_truth.json').read_text())
    files = [(folder+'/'+sample['file'], sample) for sample in truth['samples']]
    prior_folder = 'pipepaths-3d11bd427946'
    files += [(prior_folder+'/'+sample['file'], sample)
              for sample in json.loads((root/prior_folder/'ground_truth.json').read_text())['samples']
              if sample['file'] == 'brep_edge_circular.f3d']
    report = {'scope': SCOPE, 'interfaces': {
        'tag_catalog': 'decode_asm_generic_tags(blob,parsed=None)',
        'replay': 'encode_generic_tag_payload(tag) reproduces exact encoded payload bytes beginning at definition name',
        'candidates': 'match_recipe_tag_names(recipe,tag_summary,*,parsed=None)',
        'Pipe_evidence': 'inspect_pipe_recipe_tags(data,records,body,feature,features,member,members,body_identifier_summary,*,source_evidence=None)',
        'validator': 'decode_asm_recipe_tags.validate_fixtures(root,zstd_library=None)',
        'integration': 'Generic-tag catalogs and naming candidate evidence only. All initial geometry owners participate in uniqueness checks; never filter duplicate tags by coordinates, root order, or source-body membership to claim selected-source closure. All six full Pipe settings failures remain unresolved.',
        'expected_outputs': 'samples[].expected_pipe_evidence contains complete candidate output; samples[].expected_tag_catalog contains all framed initial attributes.'},
        'grammar': {
            'attribute_header': 'Typed ATTRIB_CUSTOM-attrib owner pointer4 plus owner attribute-head and reciprocal next/previous chain pointers2/3. Observed owner kinds BODY/face/edge only; all pointers stay in initial geometry.',
            'definition_fields': 'String generic_tag_attrib_def, integer schema fields[3,3,-1], literal namespace string generic_tag_attrib_def followed by one space. Definition strings are checked; no unobserved definition-object pointer is invented.',
            'payload': 'Integer term_count1/2; each term integer ASCII byte length, short ASCII string, integer stored_index, integer component_count0/1, that many signed32-range integer components, separate integerzero terminator. No remaining tokens permitted.',
            'native_correspondence': 'The full ordered term group (ASCII name,stored index,counted signed components) matches the separately framed native recipe name-table group exactly. Numeric components are never looked up as native design-object IDs.',
            'byte_encoding': 'Observed integer token4+int64, string token7+u8 byte length+ASCII bytes. Exact payload replay preserves every parsed definition/schema/namespace/term byte.',
            'namespace_scope': 'Native descriptor UUID namespaces are not literal ASM generic-tag namespaces. Both are retained separately and matches are scoped through the explicitly referenced same-asset history blob.'},
        'limitations': [
            'Circle source term(-1,index0,components[301]) matches two distinct initial edge owners: detached edge2 and an edge in the explicitly mapped source BODY. Both candidates are retained; neither is chosen.',
            'Open-line recipe entries match named source faces, while the detached auxiliary line edge is untagged. Native edge operation/intersection payload grammar remains uninterpreted, so face-name correspondences do not reconstruct a selected edge.',
            'Candidate curve-kind and endpoint-identity agreement can corroborate candidates but cannot establish selected source identity or closure.',
            'Only initial geometry and observed generic tag term counts1/2 and component counts0/1 are admitted. Known timestamp and sketch-coedge attribute layouts are independently framed and excluded without interpreting sketch text. Other custom definitions cause unresolved coverage rather than being silently skipped. History snapshots, generic-tag count2+ component arrays, non-ASCII tags and persistent regeneration are outside this stage.'],
        'samples': [], 'comparisons': [], 'malformed_guards': []}
    tag_count = term_count = 0
    unique_count = ambiguous_count = 0
    saved_circle = None

    def check(label, actual, expected):
        assert actual == expected, (label, actual, expected)
        report['comparisons'].append({'label': label, 'actual': actual, 'expected': expected, 'passed': True})

    for filename, sample in files:
        members = read_members(root/filename, zstd_library)
        stream = decode_basics(root/filename, zstd_library)['streams'][0]
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        features = stream['features']
        feature = next(f for f in features if f['kind'] == 'Pipe')
        record = next(r for r in records if r.is_primary and r.object_id == feature['object_id'])
        body = data[record.body:record.end]
        evidence = inspect_pipe_recipe_tags(data, records, body, feature, features, stream['member'], members, stream['body_asm_identifiers'])
        blob = members[evidence['history_blob_member']]
        parsed = inspect_asm(blob)
        tags = decode_asm_generic_tags(blob, parsed)
        check(filename+' complete initial generic-tag coverage', tags['unresolved'], [])
        check(filename+' all tag payloads replay byte-exactly',
              all(encode_generic_tag_payload(tag).hex() == tag['payload_hex'] for tag in tags['tags']), True)
        tag_count += len(tags['tags'])
        term_count += sum(len(tag['terms']) for tag in tags['tags'])
        api = sample['settings']
        actual_source = api['path']['members'][0]['source']
        source_body = next(b for b in stream['body_properties']['bodies'] if b['object_id'] == evidence['native_source_body_object_id'])
        check(filename+' native source body name agrees actual source getter', source_body['name'], actual_source['body_name'])
        check(filename+' source edge closure remains unknown', evidence['source_edge_is_closed'], None)
        check(filename+' source curve geometry remains unknown', evidence['source_curve_geometry'], None)
        entries = evidence['recipe_naming_correspondence']['name_entries']
        for entry in entries:
            check(filename+f" entry{entry['name_table_index']} chooses no owner", entry['selected_source_owner_record_index'], None)
            if entry['candidate_count'] == 1:
                unique_count += 1
                check(filename+f" entry{entry['name_table_index']} unique typed name owner belongs to explicit source BODY",
                      entry['candidates'][0]['body_graph_membership'], [evidence['explicit_asm_source_body_index']])
            elif entry['candidate_count'] > 1:
                ambiguous_count += 1
                check(filename+' ambiguous tuple is retained', entry['status'], 'AmbiguousStoredNamingCorrespondence')
        if api['path']['is_closed']:
            first = entries[0]
            check(filename+' exact edge naming tuple remains ambiguous', first['candidate_count'], 2)
            check(filename+' ambiguity includes detached and source BODY owners',
                  sorted(candidate['body_graph_membership'] for candidate in first['candidates']), [[], [evidence['explicit_asm_source_body_index']]])
            check(filename+' all matching edge caches have ellipse primitive', sorted({candidate['curve_kind'] for candidate in first['candidates']}), ['ellipse-curve'])
            check(filename+' every matching candidate repeats one endpoint vertex identity',
                  all(candidate['cached_endpoint_identity_same'] for candidate in first['candidates']), True)
            topology = decode_topology(parsed)
            nodes = {node['index']: node for node in topology['nodes']}
            check(filename+' every candidate cached ellipse ratio agrees Circle3D getter family',
                  all(nodes[candidate['curve_index']]['stored_axis_ratio'] == 1 for candidate in first['candidates']), True)
            if filename.endswith('/circle_full.f3d'):
                saved_circle = (data, records, body, feature, features, stream, members, parsed, blob, tags, evidence)
        else:
            check(filename+' line recipe name entries match faces rather than a selected edge',
                  sorted({candidate['owner_kind'] for entry in entries for candidate in entry['candidates']}), ['face'])
        report['samples'].append({'file': filename, 'expected_pipe_evidence': evidence, 'expected_tag_catalog': tags,
            'API_observation': {'source_type': actual_source['entity_type'],
                                'source_geometry_type': actual_source['natural_geometry']['geometry_type'],
                                'path_is_closed': api['path']['is_closed'], 'distance_one': api['distance_one'], 'distance_two': api['distance_two']},
            'API_evidence_status': 'Source getters independently corroborate candidate primitive families only; no API geometry or closedness is injected into native selected-source fields'})

    data, records, body, feature, features, stream, members, parsed, blob, tags, evidence = saved_circle
    attribute_index = evidence['recipe_naming_correspondence']['name_entries'][0]['candidates'][0]['attribute_record_index']
    attribute = parsed['records'][attribute_index]
    tokens = attribute['tokens']
    guards = [
        ('Unobserved generic tag term count', tokens[10]['offset']+1, struct.pack('<q', 3)),
        ('Explicit name byte length disagreement', tokens[11]['offset']+1, struct.pack('<q', 3)),
        ('Unobserved generic tag component count', tokens[14]['offset']+1, struct.pack('<q', 2)),
        ('Nonreciprocal attribute owner pointer', tokens[4]['offset']+1, struct.pack('<q', 3)),
        ('Wrong framed namespace literal', tokens[9]['offset']+2+len(tokens[9]['value'])-1, b'!'),
        ('Unknown custom definition cannot silently remove a naming candidate', tokens[5]['offset']+2+len(tokens[5]['value'])-1, b'!'),
        ('Nonzero generic tag term terminator', tokens[-1]['offset']+1, struct.pack('<q', 1))]
    recipe_record = next(r for r in records if r.is_primary and r.object_id == evidence['source_recipe_object_id'])
    recipe = decode_counted_recipe(data, recipe_record)
    for label, offset, replacement in guards:
        changed = bytearray(blob)
        changed[offset:offset+len(replacement)] = replacement
        rejected = decode_asm_generic_tags(bytes(changed))
        assert rejected['unresolved'], label
        try:
            match_recipe_tag_names(recipe, rejected)
        except ValueError as error:
            report['malformed_guards'].append({'label': label, 'rejected': True,
                                               'attribute_reason': rejected['unresolved'][0]['reason'],
                                               'candidate_reason': str(error)})
        else:
            raise AssertionError(label+' incomplete coverage must not yield unique naming candidates')
    wrong_mapping = copy.deepcopy(stream['body_asm_identifiers'])
    wrong_mapping['decoded'][0]['history_blob_member'] = 'DifferentAsset/Breps.BlobParts/BREP.wrong.smbh'
    try:
        inspect_pipe_recipe_tags(data, records, body, feature, features, stream['member'], members, wrong_mapping)
    except ValueError as error:
        report['malformed_guards'].append({'label': 'Cross-asset/mismatched history blob association', 'rejected': True, 'reason': str(error)})
    else:
        raise AssertionError('Mismatched source-blob namespace accepted')
    report['next_discriminating_capture'] = {
        'proposal': 'Two Pipe features in one document, selecting different top/bottom circular edges of one support body, with distinct fractions; additionally capture an open curved BRep edge as an independent open/curved contrast.',
        'capture': 'Actual rolled-back Path members/source body+edge tokens, vertex identities, natural/trimmed evaluators and all native feature refs; local archive only.',
        'purpose': 'Test whether detached-cache named copies have an additional per-feature serialized association or shared generic tags. Source-body ownership and duplicate term groups must remain visible. An open arc distinguishes primitive family from topological closure.',
        'remaining_requirement': 'An explicit typed per-feature source/recipe-operation relation is still required; exact geometry agreement among duplicated candidates alone cannot resolve selected-source closure.'}
    report['validation'] = {'saved_files': len(files), 'framed_initial_generic_tag_attributes': tag_count,
                            'framed_generic_tag_terms': term_count, 'exact_attribute_payload_replays': tag_count,
                            'unique_recipe_name_entry_correspondences': unique_count, 'ambiguous_recipe_name_entry_correspondences': ambiguous_count,
                            'comparisons_passed': len(report['comparisons']), 'malformed_guards_passed': len(report['malformed_guards']),
                            'full_Pipe_settings_failures_cleared': 0, 'selected_source_closure_claims': 0, 'new_API_calls': 0}
    return report
