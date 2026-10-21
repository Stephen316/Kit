"""Untrim face operands and separately qualified Manual loop cache provenance."""
import math
import struct
import uuid

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names, _terms_key
from decode_asm_subtypes import decode_asm_subtypes
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections, HELPER, SUPPORT
from decode_brep import decode_topology
from decode_one_face_edge_sources import _replay_recipe
from decode_parameters import read_string
from decode_patch_continuity import PATCH
from decode_recipe_components import decode_counted_recipe
from decode_selection import native_proxy_references
from decode_selection_context_recipes import TOPOLOGY, decode_selection_context_recipes
from decode_sketch import reference

UNTRIM = '4082E43B-D693-40D7-B44B-26800C9148DB'
PROXY = '2CA5A1CD-C99B-4C9B-91AF-57989148E841'
SCOPE = ('Observed Untrim owned face recipe and optional Manual edge/face recipe, '
         'explicit mapped initial cache and qualified literal alternate-cache provenance. '
         'No chronology, before-feature/current/persistent/API source identity, loop-role or regeneration claim.')


def _terms(recipe, count):
    table = recipe['name_table']
    if (len(table) != count or [e['table_index'] for e in table] != list(range(count))
            or any(len(e['terms']) != 1 or e['terms'][0]['stored_index'] != 0
                   or e['terms'][0]['stored_reference_component_count'] != 1 for e in table)):
        raise ValueError('Untrim complete counted-name framing differs')


def _face_cache(topology, body_id, face_id):
    nodes = {n['index']:n for n in topology['nodes']}
    graphs = [g for g in topology['body_graphs'] if g['body_index'] == body_id]
    if (len(graphs) != 1 or not graphs[0]['body_transform_is_identity']
            or face_id not in graphs[0]['face_indices'] or nodes[face_id]['kind'] != 'face'):
        raise ValueError('Untrim face is outside one identity-transform mapped BODY graph')
    graph = graphs[0]; face = nodes[face_id]
    loops = [nodes[i] for i in graph['loop_indices'] if nodes[i]['face_index'] == face_id]
    if not loops or face['first_loop_index'] not in {n['index'] for n in loops}:
        raise ValueError('Untrim named face lacks reciprocal loop membership')
    routes = []
    for loop in loops:
        cs = [nodes[i] for i in graph['coedge_indices'] if nodes[i]['loop_index'] == loop['index']]
        if not cs or loop['first_coedge_index'] not in {n['index'] for n in cs}:
            raise ValueError('Untrim named face loop lacks reciprocal coedges')
        for coedge in cs:
            edge = nodes[coedge['edge_index']]
            if (nodes[coedge['next_coedge_index']]['previous_coedge_index'] != coedge['index']
                    or nodes[coedge['previous_coedge_index']]['next_coedge_index'] != coedge['index']
                    or coedge['edge_index'] not in graph['edge_indices']
                    or edge['start_vertex_index'] not in graph['vertex_indices']
                    or edge['end_vertex_index'] not in graph['vertex_indices']):
                raise ValueError('Untrim named face/coedge/edge/vertex incidence differs')
            routes.append(dict(loop_record_index=loop['index'],coedge_record_index=coedge['index'],
                edge_record_index=edge['index'],start_vertex_record_index=edge['start_vertex_index'],
                end_vertex_record_index=edge['end_vertex_index']))
    surface = nodes[face['surface_index']]
    boundary_edges = []
    for identity in sorted({r['edge_record_index'] for r in routes}):
        edge = nodes[identity]
        vertices = [nodes[i] for i in sorted({edge['start_vertex_index'],edge['end_vertex_index']})]
        points = [nodes[v['point_index']] for v in vertices]
        if any(v['kind'] != 'vertex' for v in vertices) or any(p['kind'] != 'point' for p in points):
            raise ValueError('Untrim face boundary geometry lacks typed vertex/point copies')
        boundary_edges.append(dict(edge=edge,curve=nodes[edge['curve_index']],vertices=vertices,points=points))
    return dict(body_record_index=body_id,face_record_index=face_id,face=face,
        surface=surface,incidence_routes=routes,boundary_edges=boundary_edges,
        scope='Mapped initial ASM face/cache only; no qualified before-Untrim or current state')


def decode_untrim_sources(data, records, features, member, members,
                          body_identifier_summary, body_selections=None):
    result = dict(associations=[],unresolved=[],scope=SCOPE)
    candidates = [r for r in records if r.is_primary and r.class_guid == UNTRIM]
    if not candidates: return result
    grouped, metadata = {}, {}
    for r in records:
        if r.is_primary: grouped.setdefault(r.object_id,[]).append(r)
    for f in features: metadata.setdefault(f['object_id'],[]).append(f)
    def typed(identity,guid=None):
        rows = grouped.get(identity,[])
        if len(rows) != 1 or guid is not None and rows[0].class_guid != guid:
            raise ValueError('Untrim source typed reference missing, ambiguous or wrong class')
        r = rows[0]
        return r,data[r.body:r.end]
    selections = decode_body_selections(data,records)
    contexts = decode_selection_context_recipes(data,records,selections)
    mapped, cache = None, {}
    for candidate in candidates:
        owner = candidate.object_id
        try:
            rec,body = typed(owner,UNTRIM)
            if member not in members or members[member] != data or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat'):
                raise ValueError('Untrim Design member/bytes scope differs')
            fs = metadata.get(owner,[])
            if len(fs) != 1 or fs[0].get('class_guid') != UNTRIM or fs[0].get('record_offset') != rec.start:
                raise ValueError('Untrim feature metadata missing or ambiguous')
            if len(body) < 160 or body[:2] != bytes(2):
                raise ValueError('Untrim feature common prefix differs')
            manual_count = struct.unpack_from('<I',body,2)[0]
            if manual_count not in (0,1): raise ValueError('Untrim Manual proxy count outside captured family')
            at = 6+11*manual_count;binding = reference(body,at)
            typed(binding,'D91D429C-1BB5-4640-B49F-69AF14F463E9')
            mode = struct.unpack_from('<I',body,at+11)[0]
            if (mode not in (0,1,2,3) or (mode == 3) != bool(manual_count)
                    or body[at+15:at+27] != bytes(12) or struct.unpack_from('<I',body,at+27)[0] != 1):
                raise ValueError('Untrim loop-mode/face-selection count frame differs')
            face_proxy = reference(body,at+31)
            manual_proxies = [reference(body,6)] if manual_count else []
            if face_proxy in manual_proxies: raise ValueError('Untrim face and Manual proxies are not distinct')

            def selection(proxy_id, role):
                pr,proxy = typed(proxy_id,PROXY)
                ds,props = native_proxy_references(data,pr)
                if (len(ds) != 1 or props or len(proxy) != 105
                        or proxy[:6] != bytes(2)+struct.pack('<I',1)
                        or proxy[17:23] != bytes(2)+struct.pack('<I',1)
                        or proxy[34:52] != bytes(4)+struct.pack('<I',9)+bytes(10)
                        or proxy[52:56] != b'\1\1\0\0' or proxy[64:68] != b'\1\1\0\0'
                        or proxy[79:82] != b'\1\0\0' or proxy[93] != 0 or reference(proxy,94) != owner):
                    raise ValueError('Untrim singleton proxy complete framing/owner differs')
                _,secondary = typed(reference(proxy,23),'2DF7DA30-A4E4-4260-AFD1-D9C7154CB44B')
                phid,psid = reference(proxy,68),reference(proxy,82)
                _,ph = typed(phid,HELPER);_,ps = typed(psid,SUPPORT)
                if (secondary != bytes.fromhex('0000010100') or ph != bytes.fromhex('0001000000000000000000000000')
                        or len(ps) != 58 or ps[:12] != bytes(6)+b'\1\1'+struct.pack('<I',1)
                        or reference(ps,12) != ds[0] or reference(ps,31) != proxy_id or ps[-8:] != bytes(8)):
                    raise ValueError('Untrim proxy helper/support reciprocity differs')
                did = ds[0];_,descriptor = typed(did,TOPOLOGY)
                if (len(descriptor) != 276 or descriptor[:3] != bytes(3) or descriptor[3] not in (0,1)
                        or struct.unpack_from('<I',descriptor,15)[0] != 1
                        or descriptor[171:183] != struct.pack('<QI',2,1)
                        or struct.unpack_from('<I',descriptor,194)[0] != 1
                        or descriptor[209:223] != struct.pack('<I',9)+bytes(10)
                        or descriptor[223:227] != b'\1\1\0\0' or descriptor[227:235] != bytes(8)
                        or descriptor[235:239] != b'\1\1\0\0' or descriptor[250:253] != b'\1\0\0'
                        or descriptor[264] != 0 or reference(descriptor,265) != owner):
                    raise ValueError('Untrim descriptor count/trailer/owner frame differs')
                ns,pos = read_string(descriptor,19);entity,pos = read_string(descriptor,pos)
                if pos != 171 or len(ns) != 36 or len(entity) != 36:
                    raise ValueError('Untrim descriptor namespace extent differs')
                uuid.UUID(ns);uuid.UUID(entity)
                context_rows = [c for c in contexts['contexts'] if c['descriptor_object_id'] == did]
                if len(context_rows) != 1 or context_rows[0]['owner_object_id'] != owner:
                    raise ValueError('Untrim independently typed descriptor/context route unresolved')
                context = context_rows[0]
                anchor_id = reference(descriptor,198)
                found = [a for a in selections['body_anchors'] if a['object_id'] == anchor_id]
                if len(found) != 1: raise ValueError('Untrim source anchor missing or ambiguous')
                anchor = found[0];source = anchor['source_owner_object_id'];typed(source,PATCH)
                if source == owner: raise ValueError('Untrim source owner is receiving feature')
                if body_selections is not None:
                    supplied = [a for a in body_selections['body_anchors'] if a['object_id'] == anchor_id]
                    if len(supplied) != 1 or any(supplied[0][k] != anchor[k] for k in ('native_body_object_id','source_owner_object_id')):
                        raise ValueError('Untrim supplied native source anchor differs')
                dhid,dsid = reference(descriptor,239),reference(descriptor,253)
                _,dh = typed(dhid,HELPER);_,support = typed(dsid,SUPPORT)
                if (dh != bytes.fromhex('0001000000000000000000000000') or len(support) != 58
                        or support[:12] != bytes(6)+b'\1\1'+struct.pack('<I',1)
                        or reference(support,12) != source or reference(support,31) != did or support[-8:] != bytes(8)):
                    raise ValueError('Untrim descriptor source support reciprocity differs')
                rr,rb = typed(reference(descriptor,4),'7ACC2A03-0261-4879-A14A-A93D661A5BDC')
                recipe = decode_counted_recipe(data,rr)
                if _replay_recipe(recipe) != rb: raise ValueError('Untrim complete counted recipe replay differs')
                _,cb = typed(context['context_object_id'],'C46D3EEB-40E1-43FA-83DC-9CB204335417')
                return dict(role=role,selection_record_object_id=proxy_id,descriptor_object_id=did,
                    recipe_object_id=rr.object_id,recipe=recipe,full_counted_recipe_payload_hex=rb.hex(),
                    exact_full_counted_recipe_replay=True,namespace_text=ns,entity_guid_text=entity,
                    context_evidence=context,context_payload_hex=cb.hex(),
                    body_anchor_object_id=anchor_id,native_body_object_id=anchor['native_body_object_id'],
                    historical_source_owner_object_id=source,proxy_payload_hex=proxy.hex(),
                    descriptor_payload_hex=descriptor.hex(),proxy_helper_object_id=phid,proxy_support_object_id=psid,
                    proxy_support_payload_hex=ps.hex(),descriptor_helper_object_id=dhid,
                    descriptor_support_object_id=dsid,descriptor_support_payload_hex=support.hex())
            face = selection(face_proxy,'Face');manual = [selection(p,'Manual') for p in manual_proxies]
            ns,pos = read_string(body,at+42)
            if ns != str(uuid.UUID(int=0)) or body[pos:pos+3] != bytes(3):
                raise ValueError('Untrim feature namespace/dependency prefix differs')
            n = struct.unpack_from('<I',body,pos+3)[0]
            deps = [reference(body,pos+7+11*i) for i in range(n)] if n <= 5 else []
            expected = [binding,face_proxy,face['descriptor_object_id']]
            for row in manual: expected.extend([row['selection_record_object_id'],row['descriptor_object_id']])
            if n != len(expected) or deps != expected:
                raise ValueError('Untrim repeated native dependencies differ from selector roles')
            pos += 7+11*n;marker = struct.unpack_from('<I',body,pos)[0]
            label,pos = read_string(body,pos+4);index = struct.unpack_from('<Q',body,pos)[0]
            name,pos = read_string(body,pos+8)
            if marker not in (8,10) or label != 'SurfaceUntrim' or index != fs[0].get('stored_index') or name != fs[0].get('name') or len(body)-pos != 66:
                raise ValueError('Untrim feature repeated metadata/footer extent differs')
            if manual and any(any(row[k] != face[k] for k in ('body_anchor_object_id','native_body_object_id','historical_source_owner_object_id')) for row in manual):
                raise ValueError('Untrim face and Manual selectors disagree on native source route')
            _terms(face['recipe'],1)
            if face['recipe']['payload_kind'] != 'face_recipe_data' or bytes.fromhex(face['recipe']['payload_hex']) != struct.pack('<2i',0,-1):
                raise ValueError('Untrim face operation outside captured8-byte framing')
            face['operation_operands'] = dict(stored_direct_face_name_index=0,stored_final_qualifier_int32=-1,
                qualifier_semantics=None,payload_hex=face['recipe']['payload_hex'],exact_payload_replay=True)
            if mapped is None: mapped = decode_body_asm_identifiers(data,records,member,members,body_identifier_summary)
            matches = [(m,b) for m in mapped['decoded'] for b in m['bindings'] if b['native_body_object_id'] == face['native_body_object_id']]
            if len(matches) != 1: raise ValueError('Untrim source BODY lacks unique fresh same-asset mapping')
            mapping,binding = matches[0]
            supplied = [b for m in body_identifier_summary['decoded'] if m['mapping_record_object_id'] == mapping['mapping_record_object_id'] for b in m['bindings'] if b['native_body_object_id'] == face['native_body_object_id']]
            if len(supplied) != 1 or supplied[0]['asm_body_index'] != binding['asm_body_index']:
                raise ValueError('Untrim supplied ASM BODY association differs')
            blob_member,body_id = mapping['history_blob_member'],binding['asm_body_index']
            if blob_member not in cache:
                blob = members[blob_member];parsed = inspect_asm(blob)
                tags = decode_asm_generic_tags(blob,parsed=parsed,allow_fpm_tracking=True)
                topology = decode_topology(parsed,subtype_catalog=decode_asm_subtypes(blob,parsed=parsed))
                if tags['unresolved'] or topology['unresolved']:
                    raise ValueError('Untrim initial naming/topology coverage incomplete')
                cache[blob_member] = blob,parsed,tags,topology
            blob,parsed,tags,topology = cache[blob_member]
            naming = match_recipe_tag_names(face['recipe'],tags,parsed=parsed)
            entry = naming['name_entries'][0];version = None
            if entry['candidate_count'] == 1:
                candidate_face = entry['candidates'][0]
                if candidate_face['owner_kind'] != 'face' or candidate_face['body_graph_membership'] != [body_id]:
                    raise ValueError('Untrim initial face name outside mapped BODY')
                face_id = candidate_face['owner_record_index']
            elif entry['candidate_count'] == 0:
                from decode_asm_name_versions import decode_asm_name_versions
                versions = decode_asm_name_versions(blob,parsed=parsed,allow_modified_nested=True)
                if versions['unresolved']: raise ValueError('Untrim modified naming-version proof unresolved')
                wanted = _terms_key(face['recipe']['name_table'][0]['terms'])
                pairs = [v for v in versions['decoded'] if _terms_key(v['trailing_attribute']['terms']) == wanted]
                if len(pairs) != 1 or pairs[0]['initial_body_record_index'] != body_id:
                    raise ValueError('Untrim face lacks unique literal paired naming-version in mapped BODY')
                version = pairs[0];face_id = version['owner_face_record_index']
            else: raise ValueError('Untrim initial complete face name ambiguous')
            face.update(naming_correspondence=naming,literal_face_name_version=version,
                stored_initial_operand_cache=_face_cache(topology,body_id,face_id),
                qualification='Literal paired naming-version to initial-cache face correspondence' if version else 'Exact initial-cache face naming correspondence')
            # The same strict local materializer may qualify a literal alternate
            # FACE cache for Internal as well as Manual. Eligibility follows the
            # serialized journal proof, never a filename or numeric BODY ID.
            from materialize_untrim_cache import materialize_untrim_cache
            alternate = None
            try:
                candidate_view = materialize_untrim_cache(blob,initial_body_record_index=body_id,
                    stored_body_identifier=binding['stored_handle'],parsed=parsed)
            except ValueError as error:
                face['alternate_cache_status'] = dict(status='UnsupportedAlternateCache',reason=str(error),
                    scope='Initial face/name provenance remains qualified; no alternate state inferred')
            else:
                vp,vt = candidate_view['view_parsed'],candidate_view['topology']
                view_tags = decode_asm_generic_tags(blob,parsed=vp,allow_fpm_tracking=True)
                correspondence = match_recipe_tag_names(face['recipe'],view_tags,parsed=vp)
                entries = correspondence['name_entries']
                vb = candidate_view['qualified_body_view_record_index']
                if (view_tags['unresolved'] or vt['unresolved'] or len(entries) != 1
                        or entries[0]['candidate_count'] != 1):
                    raise ValueError('Untrim alternate FACE complete naming/topology unresolved')
                name = entries[0]['candidates'][0]
                if name['owner_kind'] != 'face' or name['body_graph_membership'] != [vb]:
                    raise ValueError('Untrim alternate named FACE outside qualified BODY')
                fc = _face_cache(vt,vb,name['owner_record_index'])
                fc['scope'] = 'Qualified literal nonserialized alternate cache only; chronology and source state unresolved'
                selected = {vb,name['owner_record_index'],name['attribute_record_index'],fc['surface']['index']}
                for route in fc['incidence_routes']: selected.update(route.values())
                for boundary in fc['boundary_edges']:
                    selected.update([boundary['edge']['index'],boundary['curve']['index']])
                    selected.update(n['index'] for n in boundary['vertices']+boundary['points'])
                origins = [o for o in candidate_view['origin_map'] if o['view_record_index'] in selected]
                if len(origins) != len(selected):
                    raise ValueError('Untrim alternate FACE selected origins missing or ambiguous')
                face['alternate_cache_status'] = dict(status='QualifiedLiteralAlternateCache',qualified_historical_state=None)
                face['qualified_alternate_face_candidate'] = dict(naming_correspondence=correspondence,
                    cached_face=fc,selected_cache_origins=origins,
                    alternate_cache_provenance={k:v for k,v in candidate_view.items() if k not in ('view_parsed','topology')},
                    exact_selected_source_identity=None,current_source_identity=None,persistent_source_identity=None,
                    qualified_historical_state=None,API_handle_identity=None)
                alternate = candidate_view
            manual_results = []
            for row in manual:
                recipe = row['recipe'];_terms(recipe,2)
                if recipe['payload_kind'] != 'edge_recipe_data' or bytes.fromhex(recipe['payload_hex']) != struct.pack('<7i',0,-1,1,1,-1,0,0):
                    raise ValueError('Untrim Manual operation outside captured28-byte framing')
                row['operation_operands'] = dict(stored_direct_edge_name_index=0,stored_secondary_index=-1,
                    stored_face_count=1,face_name_index=1,stored_face_secondary_index=-1,stored_endpoint_count=0,
                    stored_final_qualifier_int32=0,qualifier_semantics=None,payload_hex=recipe['payload_hex'],exact_payload_replay=True)
                route = row['context_evidence']['optional_context_recipe_route']
                if route is None: raise ValueError('Untrim Manual secondary naming recipe route absent')
                rr,_ = typed(route['recipe']['object_id'],'7ACC2A03-0261-4879-A14A-A93D661A5BDC')
                secondary = decode_counted_recipe(data,rr);_terms(secondary,2)
                if (_replay_recipe(secondary) != data[rr.body:rr.end]
                        or secondary['payload_kind'] != 'edge_recipe_data'
                        or bytes.fromhex(secondary['payload_hex']) != struct.pack('<7i',0,-1,1,1,-1,0,-1)
                        or [_terms_key(e['terms']) for e in secondary['name_table']] != [_terms_key(e['terms']) for e in recipe['name_table']]):
                    raise ValueError('Untrim Manual secondary recipe complete names/opaque qualifier framing differ')
                if alternate is None:
                    raise ValueError('Untrim Manual requires a qualified literal alternate cache')
                vp,vt = alternate['view_parsed'],alternate['topology']
                view_tags = decode_asm_generic_tags(blob,parsed=vp,allow_fpm_tracking=True)
                if view_tags['unresolved'] or vt['unresolved']:
                    raise ValueError('Untrim Manual alternate-view naming/topology incomplete')
                correspondence = match_recipe_tag_names(recipe,view_tags,parsed=vp)
                es = correspondence['name_entries']
                if len(es) != 2 or any(e['candidate_count'] != 1 for e in es):
                    raise ValueError('Untrim Manual alternate-view complete edge/face names absent or ambiguous')
                edge_name,face_name = [e['candidates'][0] for e in es]
                vb = alternate['qualified_body_view_record_index']
                if edge_name['owner_kind'] != 'edge' or face_name['owner_kind'] != 'face' or any(e['body_graph_membership'] != [vb] for e in (edge_name,face_name)):
                    raise ValueError('Untrim Manual names outside explicitly qualified alternate BODY')
                vn = {n['index']:n for n in vt['nodes']};edge = vn[edge_name['owner_record_index']]
                face_cache = _face_cache(vt,vb,face_name['owner_record_index'])
                routes = [r for r in face_cache['incidence_routes'] if r['edge_record_index'] == edge['index']]
                if len(routes) != 1: raise ValueError('Untrim Manual named edge lacks one face-loop incidence')
                coedge,loop = vn[routes[0]['coedge_record_index']],vn[routes[0]['loop_record_index']]
                curve = vn[edge['curve_index']]
                if (coedge['partner_index'] is not None or edge['first_coedge_index'] != coedge['index']
                        or coedge['next_coedge_index'] != coedge['index'] or coedge['previous_coedge_index'] != coedge['index']
                        or edge['start_vertex_index'] != edge['end_vertex_index']
                        or curve['kind'] != 'ellipse-curve' or curve['stored_axis_ratio'] != 1.):
                    raise ValueError('Untrim Manual cache is outside captured single-edge circular loop')
                vertex = vn[edge['start_vertex_index']];point = vn[vertex['point_index']]
                if point['kind'] != 'point' or not math.isclose(edge['end_parameter']-edge['start_parameter'],2*math.pi,abs_tol=1e-12):
                    raise ValueError('Untrim Manual closed-loop endpoint/domain differs')
                values = curve['raw_origin']+curve['normal']+curve['stored_reference_axis']+point['raw_origin']+[curve['raw_major_radius'],edge['start_parameter'],edge['end_parameter']]
                if any(not math.isfinite(v) for v in values) or curve['raw_major_radius'] <= 0:
                    raise ValueError('Untrim Manual loop cache contains nonfinite/degenerate circle')
                selected_ids = [vb,face_name['owner_record_index'],edge['index'],coedge['index'],loop['index'],curve['index'],vertex['index'],point['index'],edge_name['attribute_record_index'],face_name['attribute_record_index']]
                origins = [o for o in alternate['origin_map'] if o['view_record_index'] in selected_ids]
                if len(origins) != len(set(selected_ids)):
                    raise ValueError('Untrim Manual selected cache origins missing or ambiguous')
                edge_origin = next(o for o in origins if o['view_record_index'] == edge['index'])
                if edge_origin['section'] != 'trailing_states':
                    raise ValueError('Untrim Manual named edge is not the observed trailing cache operand')
                literal_entries = [e for state in alternate['canonical_history']['journal_states'] if state['delta_state_slot'] == 0
                    for e in state['entries'] if e['pointer_sides'][0]['stored_geometry_entity_ordinal'] == edge_origin['geometry_entity_ordinal']]
                if len(literal_entries) != 1 or literal_entries[0]['pointer_sides'][1]['stored_geometry_entity_ordinal'] != -1:
                    raise ValueError('Untrim Manual named edge lacks the explicit null-opposite literal slot0 entry')
                row.update(secondary_recipe=secondary,alternate_naming_correspondence=correspondence,
                    named_edge_literal_journal_context=dict(delta_state_slot=0,**literal_entries[0]),
                    initial_edge_alias=None,
                    qualification='Exact named operands in a strictly closed literal slot0/side0 alternate cache; no chronology',
                    geometric_loop_candidate=dict(body_view_record_index=vb,face_view_record_index=face_name['owner_record_index'],
                        loop_view_record_index=loop['index'],coedge_view_record_index=coedge['index'],edge_view_record_index=edge['index'],
                        curve_view_record_index=curve['index'],vertex_view_record_index=vertex['index'],point_view_record_index=point['index'],
                        geometry=curve,raw_endpoint_point=point['raw_origin'],parameter_domain=[edge['start_parameter'],edge['end_parameter']],
                        stored_edge_reversal=edge['is_reversed'],stored_coedge_reversal=coedge['is_reversed'],
                        semantic_loop_role=None,API_manual_loop_identity=None),
                    selected_cache_origins=origins,alternate_cache_provenance={k:v for k,v in alternate.items() if k not in ('view_parsed','topology')},
                    manual_selection_kind='Stored edge-with-one-face recipe; geometric loop candidate qualified separately',
                    exact_selected_source_identity=None,qualified_historical_state=None,current_source_identity=None,persistent_source_identity=None,API_handle_identity=None)
                manual_results.append(row)
            result['associations'].append(dict(owner_object_id=owner,face_operand=face,manual_loop_operands=manual_results,
                stored_loop_type_code=mode,repeated_dependency_object_ids=deps,feature_payload_hex=body.hex(),
                stored_metadata_marker=marker,native_body_object_id=face['native_body_object_id'],
                historical_source_owner_object_id=face['historical_source_owner_object_id'],mapping_record_object_id=mapping['mapping_record_object_id'],
                history_blob_member=blob_member,explicit_asm_body_index=body_id,
                exact_selected_source_identity=None,current_source_identity=None,persistent_source_identity=None,
                qualified_historical_state=None,API_handle_identity=None,scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
            result['unresolved'].append(dict(owner_object_id=owner,reason=str(error)))
    return result
