"""Observed bounded-face Offset sources; no API/native face identity assertion."""
import struct
import uuid

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names, _terms_key
from decode_asm_subtypes import decode_asm_subtypes
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections, HELPER, SUPPORT
from decode_brep import decode_topology
from decode_one_face_edge_sources import _replay_recipe
from decode_owned_surface_selection import decode_owned_surface_selection
from decode_parameters import read_string
from decode_recipe_components import decode_counted_recipe
from decode_selection import native_proxy_references
from decode_selection_context_recipes import TOPOLOGY
from decode_sketch import reference
from decode_untrim_sources import _face_cache

OFFSET = '1589BC73-D484-4A6E-8E69-2A1531E845F5'
PROXY = '2CA5A1CD-C99B-4C9B-91AF-57989148E841'
SCOPE = ('Observed singleton SurfaceOffset owned bounded-face recipe, complete named face/boundary '
         'operands and reciprocal incidence in explicitly mapped initial ASM cache. Actual controls '
         'come from three nonzero planar-source captures; zero-offset/API-to-VBL witnesses remain '
         'unproved. No current/persistent/API source identity, historical state or regeneration claim.')


def decode_surface_offset_face_operands(recipe):
    """Bounded counted grammar with observed children, preserving literal order.

    This admits only the observed full/simple edge branches. Table indices are
    read and checked, never supplied by a geometric or positional name guess.
    """
    raw = bytes.fromhex(recipe['payload_hex']);table = recipe['name_table']
    if recipe['payload_kind'] != 'bounded_face_recipe_data' or not 12 <= len(raw) <= 16384 or len(raw)%4:
        raise ValueError('Offset bounded-face operation extent/alignment unsupported')
    if [e['table_index'] for e in table] != list(range(len(table))) or not 1 <= len(table) <= 33:
        raise ValueError('Offset bounded-face complete name-table framing differs')
    for entry in table:
        if not 1 <= len(entry['terms']) <= 16:
            raise ValueError('Offset bounded-face name group count outside bounded grammar')
        _terms_key(entry['terms'])
    words = struct.unpack('<'+'i'*(len(raw)//4),raw);cursor = 0;replay = []
    def read():
        nonlocal cursor
        if cursor >= len(words): raise ValueError('Offset bounded-face operation truncated')
        value = words[cursor];cursor += 1;replay.append(value);return value
    def expect(value):
        actual = read()
        if actual != value: raise ValueError('Offset bounded-face sentinel/count branch differs')
        return actual
    def name():
        value = read()
        if not 0 <= value < len(table): raise ValueError('Offset bounded-face name reference leaves complete table')
        return value
    face_name = name();expect(-1);boundary_count = read()
    if not 1 <= boundary_count <= 32 or len(table) != boundary_count+1:
        raise ValueError('Offset counted boundary/name-table sizes disagree or exceed bounds')
    def simple_edge():
        start = cursor;identity = name();expect(-1);expect(0);expect(0);expect(-1)
        return dict(name_table_index=identity,stored_secondary_index=-1,stored_face_count=0,
            stored_endpoint_count=0,stored_final_qualifier_int32=-1,qualifier_semantics=None,
            relative_offset=start*4,payload_hex=raw[start*4:cursor*4].hex())
    def vertex(edge_name):
        start = cursor;expect(-1);expect(1);ref = name();expect(-1);expect(2)
        if ref != face_name: raise ValueError('Offset endpoint face reference differs from outer FACE')
        nested = [simple_edge(),simple_edge()];expect(0)
        ids = [e['name_table_index'] for e in nested]
        if len(set(ids)) != 2 or ids.count(edge_name) != 1:
            raise ValueError('Offset endpoint nested names lack direct edge and distinct adjacent edge')
        return dict(stored_direct_vertex_name_index=-1,stored_face_count=1,face_name_index=ref,
            stored_face_secondary_index=-1,stored_edge_count=2,nested_edges=nested,
            stored_inline_edge_name_order=ids,stored_terminal_int32=0,
            adjacent_edge_name_index=next(i for i in ids if i != edge_name),
            relative_offset=start*4,payload_hex=raw[start*4:cursor*4].hex())
    children = []
    for ordinal in range(boundary_count):
        start = cursor;identity = name();expect(-1);face_count = read()
        if face_count not in (0,1): raise ValueError('Offset boundary edge face-count branch unsupported')
        refs = []
        if face_count:
            ref = name();expect(-1)
            if ref != face_name: raise ValueError('Offset child face name differs from outer FACE')
            refs = [ref]
        endpoint_count = read()
        if (face_count,endpoint_count) not in ((0,0),(1,2)):
            raise ValueError('Offset child full/simple endpoint branch unsupported')
        endpoints = [vertex(identity) for _ in range(endpoint_count)];expect(-1)
        if endpoints and len({v['adjacent_edge_name_index'] for v in endpoints}) != 2:
            raise ValueError('Offset full edge endpoint operands repeat one adjacent edge')
        children.append(dict(boundary_operand_ordinal=ordinal,name_table_index=identity,
            stored_secondary_index=-1,stored_face_count=face_count,face_name_indices=refs,
            stored_endpoint_count=endpoint_count,endpoint_operands=endpoints,
            stored_final_qualifier_int32=-1,qualifier_semantics=None,relative_offset=start*4,
            payload_hex=raw[start*4:cursor*4].hex()))
    ids = [e['name_table_index'] for e in children]
    if len(set(ids)) != boundary_count or set(ids) | {face_name} != set(range(len(table))) or face_name in ids:
        raise ValueError('Offset boundary names do not exhaust the complete distinct non-FACE names')
    if any(v['adjacent_edge_name_index'] not in ids for e in children for v in e['endpoint_operands']):
        raise ValueError('Offset nested endpoint edge reference leaves outer boundary set')
    if cursor != len(words) or struct.pack('<'+'i'*len(replay),*replay) != raw:
        raise ValueError('Offset whole bounded-face operation replay/extent differs')
    return dict(stored_direct_face_name_index=face_name,stored_secondary_index=-1,
        stored_boundary_edge_count=boundary_count,boundary_edges=children,
        stored_boundary_name_order=ids,payload_hex=raw.hex(),exact_full_operation_payload_replay=True,
        scope='Complete observed full/simple operand grammar; literal qualifiers retained without history or traversal semantics')


def decode_surface_offset_sources(data, records, features, member, members,
                                  body_identifier_summary, body_selections=None):
    out = dict(associations=[],unresolved=[],scope=SCOPE)
    candidates = [r for r in records if r.is_primary and r.class_guid == OFFSET]
    if not candidates: return out
    grouped,metadata = {},{}
    for r in records:
        if r.is_primary: grouped.setdefault(r.object_id,[]).append(r)
    for f in features: metadata.setdefault(f['object_id'],[]).append(f)
    def typed(identity,guid=None):
        rows = grouped.get(identity,[])
        if len(rows) != 1 or guid is not None and rows[0].class_guid != guid:
            raise ValueError('Offset source typed reference missing, ambiguous or wrong class')
        r = rows[0];return r,data[r.body:r.end]
    anchors = decode_body_selections(data,records)['body_anchors'];mapped = None;cache = {}
    for candidate in candidates:
        owner = candidate.object_id
        try:
            rec,body = typed(owner,OFFSET)
            if member not in members or members[member] != data or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat'):
                raise ValueError('Offset Design member/byte scope differs')
            fs = metadata.get(owner,[])
            if len(fs) != 1 or fs[0].get('class_guid') != OFFSET or fs[0].get('record_offset') != rec.start:
                raise ValueError('Offset feature metadata missing or ambiguous')
            if (len(body) < 160 or body[:6] != bytes.fromhex('000100000000') or body[6] not in (0,1)
                    or body[7] not in (0,1) or body[19:23] != bytes(4) or body[38:42] != bytes(4)
                    or struct.unpack_from('<I',body,23)[0] != 1 or struct.unpack_from('<I',body,42)[0] != 1):
                raise ValueError('Offset feature observed control/result/input frame differs')
            binding = reference(body,8);typed(binding,'D91D429C-1BB5-4640-B49F-69AF14F463E9')
            result_anchor = reference(body,27);typed(result_anchor,'D26351F0-5940-4D23-AA20-2C35475A6D9E')
            results = [a for a in anchors if a['object_id'] == result_anchor]
            if len(results) != 1 or results[0]['source_owner_object_id'] != owner:
                raise ValueError('Offset owned result anchor source disagrees')
            proxy_id = reference(body,46);pr,proxy = typed(proxy_id,PROXY)
            ids,props = native_proxy_references(data,pr)
            if (len(ids) != 1 or props or len(proxy) != 105
                    or proxy[:6] != bytes(2)+struct.pack('<I',1) or proxy[17:23] != bytes(2)+struct.pack('<I',1)
                    or proxy[34:52] != bytes(4)+struct.pack('<I',65)+bytes(10)
                    or proxy[52:56] != b'\1\1\0\0' or proxy[64:68] != b'\1\1\0\0'
                    or proxy[79:82] != b'\1\0\0' or proxy[93] != 0 or reference(proxy,94) != owner):
                raise ValueError('Offset singleton proxy complete framing/owner differs')
            _,secondary = typed(reference(proxy,23),'2DF7DA30-A4E4-4260-AFD1-D9C7154CB44B')
            phid,psid = reference(proxy,68),reference(proxy,82);_,ph = typed(phid,HELPER);_,ps = typed(psid,SUPPORT)
            if (secondary != bytes.fromhex('0000010100') or ph != bytes.fromhex('0001000000000000000000000000')
                    or len(ps) != 58 or ps[:12] != bytes(6)+b'\1\1'+struct.pack('<I',1)
                    or reference(ps,12) != ids[0] or reference(ps,31) != proxy_id or ps[-8:] != bytes(8)):
                raise ValueError('Offset proxy secondary/helper/support reciprocity differs')
            did = ids[0];_,descriptor = typed(did,TOPOLOGY)
            if (len(descriptor) != 276 or descriptor[:4] != bytes(4)
                    or descriptor[209:223] != struct.pack('<I',65)+bytes(10)
                    or descriptor[223:227] != b'\1\1\0\0' or descriptor[227:235] != bytes(8)
                    or descriptor[235:239] != b'\1\1\0\0' or descriptor[250:253] != b'\1\0\0'
                    or descriptor[264] != 0 or reference(descriptor,265) != owner):
                raise ValueError('Offset descriptor complete trailer/owner framing differs')
            owned = decode_owned_surface_selection(data,records,proxy_id,owner,face_recipe_kind='bounded_face_recipe_data')
            if owned['kind'] != 'Face' or owned['face']['descriptor_object_id'] != did:
                raise ValueError('Offset independently owned singleton face route differs')
            route = owned['face'];anchor_id = route['body_anchor_object_id']
            selected = [a for a in anchors if a['object_id'] == anchor_id]
            if len(selected) != 1 or any(selected[0][k] != route[k] for k in ('native_body_object_id','source_owner_object_id')):
                raise ValueError('Offset source anchor identity differs')
            if body_selections is not None:
                supplied = [a for a in body_selections['body_anchors'] if a['object_id'] == anchor_id]
                if len(supplied) != 1 or any(supplied[0][k] != route[k] for k in ('native_body_object_id','source_owner_object_id')):
                    raise ValueError('Offset supplied source anchor identity differs')
            source_owner = route['source_owner_object_id'];typed(source_owner)
            if source_owner == owner: raise ValueError('Offset source owner equals receiving feature')
            dhid,dsid = reference(descriptor,239),reference(descriptor,253);_,dh = typed(dhid,HELPER);_,ds = typed(dsid,SUPPORT)
            if (dh != bytes.fromhex('0001000000000000000000000000') or len(ds) != 58
                    or ds[:12] != bytes(6)+b'\1\1'+struct.pack('<I',1)
                    or reference(ds,12) != source_owner or reference(ds,31) != did or ds[-8:] != bytes(8)):
                raise ValueError('Offset descriptor/source support reciprocity differs')
            rr,rb = typed(route['recipe']['object_id'],'7ACC2A03-0261-4879-A14A-A93D661A5BDC')
            recipe = decode_counted_recipe(data,rr);operands = decode_surface_offset_face_operands(recipe)
            if _replay_recipe(recipe) != rb: raise ValueError('Offset complete counted recipe replay differs')
            ns,pos = read_string(body,57)
            if ns != str(uuid.UUID(int=0)) or body[pos:pos+3] != bytes(3) or struct.unpack_from('<I',body,pos+3)[0] != 3:
                raise ValueError('Offset feature nil namespace/dependency count differs')
            deps = [reference(body,pos+7+11*i) for i in range(3)]
            if deps != [binding,proxy_id,did]: raise ValueError('Offset repeated native aliases differ')
            pos += 40
            if struct.unpack_from('<I',body,pos)[0] != 8: raise ValueError('Offset repeated metadata marker differs')
            label,pos = read_string(body,pos+4);index = struct.unpack_from('<Q',body,pos)[0];name,pos = read_string(body,pos+8)
            if label != 'SurfaceOffset' or index != fs[0].get('stored_index') or name != fs[0].get('name') or len(body)-pos != 66:
                raise ValueError('Offset repeated metadata/name/footer extent differs')
            if mapped is None: mapped = decode_body_asm_identifiers(data,records,member,members,body_identifier_summary)
            choices = [(m,b) for m in mapped['decoded'] for b in m['bindings'] if b['native_body_object_id'] == route['native_body_object_id']]
            if len(choices) != 1: raise ValueError('Offset native source BODY lacks unique fresh same-asset mapping')
            mapping,binding_row = choices[0]
            supplied = [b for m in body_identifier_summary['decoded'] if m['mapping_record_object_id'] == mapping['mapping_record_object_id']
                for b in m['bindings'] if b['native_body_object_id'] == route['native_body_object_id']]
            if len(supplied) != 1 or supplied[0]['asm_body_index'] != binding_row['asm_body_index']:
                raise ValueError('Offset supplied initial BODY association differs')
            blob_member,body_id = mapping['history_blob_member'],binding_row['asm_body_index']
            if blob_member not in cache:
                blob = members[blob_member];parsed = inspect_asm(blob)
                tags = decode_asm_generic_tags(blob,parsed=parsed,allow_fpm_tracking=True)
                topology = decode_topology(parsed,subtype_catalog=decode_asm_subtypes(blob,parsed=parsed))
                if tags['unresolved']: raise ValueError('Offset source complete initial naming coverage unresolved')
                cache[blob_member] = blob,parsed,tags,topology
            blob,parsed,tags,topology = cache[blob_member]
            naming = match_recipe_tag_names(recipe,tags,parsed=parsed)
            entries = {e['name_table_index']:e for e in naming['name_entries']}
            if set(entries) != set(range(len(recipe['name_table']))) or any(e['candidate_count'] != 1 for e in entries.values()):
                raise ValueError('Offset complete FACE/boundary names absent or globally ambiguous')
            face_id = entries[operands['stored_direct_face_name_index']]['candidates'][0]['owner_record_index']
            edge_names = operands['stored_boundary_name_order']
            for index,entry in entries.items():
                named = entry['candidates'][0]
                if named['owner_kind'] != ('face' if index == operands['stored_direct_face_name_index'] else 'edge') or named['body_graph_membership'] != [body_id]:
                    raise ValueError('Offset named operands are not typed members of explicitly mapped BODY')
            nodes = {n['index']:n for n in topology['nodes']}
            face_cache = _face_cache(topology,body_id,face_id)
            face_cache['scope'] = 'Mapped initial SurfaceOffset source FACE cache; no qualified before-feature/current state or API identity'
            face_edges = {r['edge_record_index'] for r in face_cache['incidence_routes']}
            edge_ids = [entries[i]['candidates'][0]['owner_record_index'] for i in edge_names]
            if set(edge_ids) != face_edges or len(face_cache['incidence_routes']) != operands['stored_boundary_edge_count']:
                raise ValueError('Offset outer boundary operands do not exhaust the named FACE boundary')
            boundary_routes = []
            for child,eid in zip(operands['boundary_edges'],edge_ids):
                routes = [r for r in face_cache['incidence_routes'] if r['edge_record_index'] == eid]
                if len(routes) != 1: raise ValueError('Offset named boundary edge lacks unique face coedge')
                coedge = nodes[routes[0]['coedge_record_index']];edge = nodes[eid]
                if coedge['partner_index'] is not None or edge['first_coedge_index'] != coedge['index']:
                    raise ValueError('Offset boundary edge is outside captured unpartnered source loop')
                intersections = []
                for ordinal,vertex_operand in enumerate(child['endpoint_operands']):
                    adjacent_id = entries[vertex_operand['adjacent_edge_name_index']]['candidates'][0]['owner_record_index']
                    adjacent = nodes[adjacent_id]
                    common = {edge['start_vertex_index'],edge['end_vertex_index']} & {adjacent['start_vertex_index'],adjacent['end_vertex_index']}
                    if len(common) != 1: raise ValueError('Offset full-edge endpoint incidence is not unique')
                    vertex_id = next(iter(common));vertex = nodes[vertex_id];point = nodes[vertex['point_index']]
                    intersections.append(dict(endpoint_operand_ordinal=ordinal,vertex_record_index=vertex_id,
                        point_record_index=point['index'],raw_point=point['raw_origin'],
                        stored_inline_edge_name_order=vertex_operand['stored_inline_edge_name_order'],
                        adjacent_edge_name_index=vertex_operand['adjacent_edge_name_index'],adjacent_edge_record_index=adjacent_id,
                        stored_edge_endpoint_role='Start' if vertex_id == edge['start_vertex_index'] else 'End'))
                if intersections and (len({r['vertex_record_index'] for r in intersections}) != 2 or {r['vertex_record_index'] for r in intersections} != {edge['start_vertex_index'],edge['end_vertex_index']}):
                    raise ValueError('Offset full-edge vertex operands do not exhaust distinct stored endpoints')
                boundary_routes.append(dict(boundary_operand_ordinal=child['boundary_operand_ordinal'],name_table_index=child['name_table_index'],
                    edge_record_index=eid,coedge_record_index=coedge['index'],loop_record_index=coedge['loop_index'],
                    stored_edge_reversal=edge['is_reversed'],stored_coedge_reversal=coedge['is_reversed'],endpoint_incidence=intersections))
            if len({r['loop_record_index'] for r in boundary_routes}) != 1:
                raise ValueError('Offset boundary children do not share one reciprocal face loop')
            coedge_ids = [r['coedge_record_index'] for r in boundary_routes]
            next_order = all(nodes[a]['next_coedge_index'] == b for a,b in zip(coedge_ids,coedge_ids[1:]+coedge_ids[:1]))
            previous_order = all(nodes[a]['previous_coedge_index'] == b for a,b in zip(coedge_ids,coedge_ids[1:]+coedge_ids[:1]))
            if not next_order and not previous_order:
                raise ValueError('Offset literal boundary child order does not form a reciprocal loop cycle')
            matched_tags = []
            for index,entry in entries.items():
                identity = entry['candidates'][0]['attribute_record_index']
                rows = [t for t in tags['tags'] if t['attribute_record_index'] == identity]
                if len(rows) != 1: raise ValueError('Offset complete named attribute provenance ambiguous')
                matched_tags.append(dict(name_table_index=index,tag=rows[0]))
            geometry_ids = {body_id,face_id,face_cache['surface']['index']}
            for boundary in face_cache['boundary_edges']:
                geometry_ids.update([boundary['edge']['index'],boundary['curve']['index']])
                geometry_ids.update(n['index'] for n in boundary['vertices']+boundary['points'])
            for r in face_cache['incidence_routes']: geometry_ids.update(r.values())
            for item in matched_tags:
                tag = item['tag']
                geometry_ids.update(tag['owner_attribute_chain'])
                geometry_ids.update(tag.get('nested_attribute_record_indices',[]))
            origins = [dict(record_index=i,kind=parsed['records'][i]['name'],section=parsed['records'][i]['section'],
                record_offset=parsed['records'][i]['offset'],record_end_offset=parsed['records'][i]['end_offset']) for i in sorted(geometry_ids)]
            if any(r['section'] != 'geometry' for r in origins):
                raise ValueError('Offset named geometry/attribute origin leaves initial source section')
            native_ids = [owner,proxy_id,did,rr.object_id,binding,result_anchor,anchor_id,source_owner,
                route['native_body_object_id'],phid,psid,dhid,dsid,reference(proxy,23)]+route['context_record_object_ids']
            native_origins = []
            for identity in sorted(set(native_ids)):
                r,_ = typed(identity)
                native_origins.append(dict(object_id=r.object_id,class_guid=r.class_guid,record_offset=r.start,
                    body_offset=r.body,end_offset=r.end))
            out['associations'].append(dict(owner_object_id=owner,selection_record_object_id=proxy_id,descriptor_object_id=did,
                recipe_object_id=rr.object_id,recipe=recipe,operation_operands=operands,full_counted_recipe_payload_hex=rb.hex(),
                exact_full_counted_recipe_replay=True,naming_correspondence=naming,matched_name_attributes=matched_tags,
                boundary_incidence=boundary_routes,stored_boundary_order_relation='NextCoedge' if next_order else 'PreviousCoedge',
                cached_face=face_cache,source_record_origins=origins,native_record_origins=native_origins,
                source_geometry_diagnostics=topology['unresolved'],
                source_geometry_diagnostics_scope='All initial geometry/topology diagnostics in the explicitly referenced same-asset blob, including unselected BODYs/faces; selected FACE geometry status is separate',
                surface_geometry_status=next(a['geometry_status'] for g in topology['body_graphs'] if g['body_index'] == body_id
                    for a in g['analytic_surfaces'] if a['face_index'] == face_id),
                body_anchor_object_id=anchor_id,native_body_object_id=route['native_body_object_id'],
                historical_source_owner_object_id=source_owner,mapping_record_object_id=mapping['mapping_record_object_id'],
                history_blob_member=blob_member,explicit_asm_body_index=body_id,native_stored_body_identifier=binding_row['stored_handle'],
                result_anchor_object_id=result_anchor,typed_native_selection=owned,
                feature_payload_hex=body.hex(),proxy_payload_hex=proxy.hex(),descriptor_payload_hex=descriptor.hex(),
                proxy_helper_object_id=phid,proxy_support_object_id=psid,descriptor_helper_object_id=dhid,descriptor_support_object_id=dsid,
                proxy_support_payload_hex=ps.hex(),descriptor_support_payload_hex=ds.hex(),
                repeated_dependency_object_ids=deps,exact_selected_source_identity=None,API_handle_identity=None,
                current_source_identity=None,persistent_source_identity=None,qualified_historical_state=None,
                traversal=None,future_zero_offset_VBL_witness_binding=None,scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error,StopIteration) as error:
            out['unresolved'].append(dict(owner_object_id=owner,reason=str(error)))
    return out
