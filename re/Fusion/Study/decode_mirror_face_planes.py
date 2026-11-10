"""Named initial-cache planar BRepFace support for the captured BODY Mirror.

The native anchored BODY and complete counted name select the cached FACE before
geometry is read. Support record sources remain separate from anchor ownership.
Legacy Mirror settings and their unresolved native plane geometry stay intact.
"""
import math
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import ANCHOR, BODY, CONTEXT, HELPER, SUPPORT, decode_body_selections
from decode_brep import decode_topology
from decode_mirror_modes import MIRROR, decode_mirror_modes
from decode_one_face_edge_sources import _replay_recipe
from decode_owned_surface_selection import decode_owned_surface_selection
from decode_recipe_components import decode_counted_recipe
from decode_selection import known_construction_entities, native_proxy_references
from decode_sketch import attributes, reference
from decode_untrim_sources import _face_cache

CONTROL='C444E6AD-33DC-4877-B037-A3A5518856B1'
PROXY='2CA5A1CD-C99B-4C9B-91AF-57989148E841'
FACE_DESCRIPTOR='5662F619-2281-4AD9-93DC-1FCFDA1062E7'
RECIPE='7ACC2A03-0261-4879-A14A-A93D661A5BDC'
SCOPE=('Observed BODY Mirror singleton planar face support through an owned recipe/context/anchor, '
       'same-asset stored BODY identifier, complete initial FACE name and reciprocal boundary; '
       'raw cache plane only, without current/historical-state, API handle, occurrence placement '
       'or reflection/regeneration identity')


def decode_mirror_face_planes(data,records,features,member,members,body_blob_bindings):
    """Return decoded/unresolved/scope evidence; never mutate legacy settings."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    grouped,metadata={},{}
    for rec in records:
        if rec.is_primary:grouped.setdefault(rec.object_id,[]).append(rec)
    for feature in features:metadata.setdefault(feature['object_id'],[]).append(feature)

    def typed(identity,guid=None):
        rows=grouped.get(identity,[])
        if len(rows)!=1 or guid is not None and rows[0].class_guid!=guid:
            raise ValueError('Mirror FACE plane typed identity missing, duplicate or wrong class')
        rec=rows[0]
        return rec,data[rec.body:rec.end]

    def raw(rec):
        return dict(object_id=rec.object_id,class_guid=rec.class_guid,record_offset=rec.start,
            body_offset=rec.body,end_offset=rec.end,payload_hex=data[rec.body:rec.end].hex())

    mapped,known,selections=None,None,None
    for candidate in records:
        if not candidate.is_primary or candidate.class_guid!=MIRROR:continue
        owner=candidate.object_id
        try:
            rec,body=typed(owner,MIRROR)
            if body[0]!=0 or body[1] not in (0,1):
                raise ValueError('Mirror FACE plane common feature prefix differs')
            props,cursor=attributes(body,2) if body[1] else ({},2)
            if props:raise ValueError('Mirror FACE plane feature attributes outside captured family')
            control_id=reference(body,cursor)
            control_record,control=typed(control_id,CONTROL)
            if len(control)!=133:
                raise ValueError('Mirror FACE plane controller extent differs')
            proxy_id=reference(control,14)
            proxy_record,proxy=typed(proxy_id,PROXY)
            ids,proxy_props=native_proxy_references(data,proxy_record)
            # Non-face Mirror supports remain solely with their existing reader.
            if len(ids)==1 and len(grouped.get(ids[0],[]))==1 and grouped[ids[0]][0].class_guid!=FACE_DESCRIPTOR:
                continue
            if (proxy_props or len(ids)!=1 or len(proxy)!=105 or proxy[:2]!=bytes(2)
                    or reference(proxy,94)!=owner):
                raise ValueError('Mirror FACE plane owned singleton proxy differs')
            descriptor_record,descriptor=typed(ids[0],FACE_DESCRIPTOR)
            fs=metadata.get(owner,[])
            if (len(fs)!=1 or fs[0].get('class_guid')!=MIRROR or fs[0].get('record_offset')!=rec.start
                    or fs[0].get('kind')!='Mirror'):
                raise ValueError('Mirror FACE plane receiving metadata missing or ambiguous')
            if member not in members or members[member]!=data or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat'):
                raise ValueError('Mirror FACE plane Design member/bytes scope differs')
            if known is None:known=known_construction_entities(data,records,features)
            settings=decode_mirror_modes(data,records,body,fs[0],known,features)
            if (settings['pattern_entity_type_code']!=2 or settings['pattern_compute_option_code']!=2
                    or settings['plane'] is not None or settings['is_combine'] is not False
                    or settings['plane_selection_record_object_id']!=proxy_id):
                raise ValueError('Mirror FACE plane only captured BODY/noncombine mode is qualified')
            owned=decode_owned_surface_selection(data,records,proxy_id,owner,face_recipe_kind='face_recipe_data')
            source=owned['face'];context=owned['typed_context']
            if (owned['kind']!='Face' or source['descriptor_object_id']!=ids[0]
                    or source!= {k:v for k,v in settings['plane_source'].items() if k not in
                        ('kind','selection_object_id','plane_geometry','geometry_status')}):
                raise ValueError('Mirror FACE plane independent selector and common source disagree')
            if (len(descriptor)!=276 or descriptor[:4]!=bytes(4)
                    or struct.unpack_from('<I',descriptor,15)[0]!=1
                    or descriptor[223:227]!=b'\1\1\0\0' or descriptor[235:239]!=b'\1\1\0\0'
                    or descriptor[250:253]!=b'\1\0\0' or descriptor[264]!=0
                    or reference(descriptor,265)!=owner):
                raise ValueError('Mirror FACE plane descriptor full header/trailer markers differ')
            if context['optional_context_recipe_route'] is not None:
                raise ValueError('Mirror FACE plane captured context has an absent secondary route')
            context_record,context_body=typed(context['context_object_id'],CONTEXT)
            if len(context_body)!=171:
                raise ValueError('Mirror FACE plane captured context extent differs')
            helper_id,support_id=reference(descriptor,239),reference(descriptor,253)
            helper_record,helper=typed(helper_id,HELPER)
            support_record,support=typed(support_id,SUPPORT)
            if (helper!=bytes.fromhex('0001000000000000000000000000')
                    or len(support)!=58 or support[:12]!=bytes(6)+b'\1\1'+struct.pack('<I',1)
                    or reference(support,31)!=ids[0] or support[-8:]!=bytes(8)):
                raise ValueError('Mirror FACE plane helper/reciprocal single-source support framing differs')
            support_source_id=reference(support,12)
            support_source_record,_=typed(support_source_id)
            # This native support role is retained, never substituted for anchor ownership.
            if support_source_record.class_guid!='DD405BC2-D673-44F0-8833-5CB2A1C186C7':
                raise ValueError('Mirror FACE plane support source is not a typed captured Extrude')
            if selections is None:selections=decode_body_selections(data,records)
            anchors=[a for a in selections['body_anchors'] if a['object_id']==source['body_anchor_object_id']]
            if (len(anchors)!=1 or any(anchors[0][k]!=source[k] for k in ('native_body_object_id','source_owner_object_id'))):
                raise ValueError('Mirror FACE plane independent historical anchor route differs')
            anchor=anchors[0]
            anchor_record,ab=typed(anchor['object_id'],ANCHOR)
            native_body_record,_=typed(anchor['native_body_object_id'],BODY)
            anchor_owner_record,_=typed(anchor['source_owner_object_id'],'DD405BC2-D673-44F0-8833-5CB2A1C186C7')
            if len(ab)!=102 or reference(ab,80)!=anchor['native_body_object_id'] or reference(ab,91)!=anchor['source_owner_object_id']:
                raise ValueError('Mirror FACE plane anchor extent/BODY/owner copies disagree')
            recipe_record,recipe_body=typed(reference(descriptor,4),RECIPE)
            recipe=decode_counted_recipe(data,recipe_record)
            if (recipe['stored_header_fields']!=[1,3] or recipe['payload_kind']!='face_recipe_data'
                    or recipe['payload_hex']!='00000000ffffffff' or len(recipe['name_table'])!=1
                    or recipe['name_table'][0]['table_index']!=0 or len(recipe['name_table'][0]['terms'])!=1
                    or recipe['name_table'][0]['terms'][0]['stored_reference_component_count']!=1
                    or _replay_recipe(recipe)!=recipe_body):
                raise ValueError('Mirror FACE plane full counted direct-name recipe/replay differs')
            if mapped is None:mapped=decode_body_asm_identifiers(data,records,member,members,body_blob_bindings)
            choices=[(m,b) for m in mapped['decoded'] for b in m['bindings']
                if b['native_body_object_id']==anchor['native_body_object_id']]
            if len(choices)!=1:
                raise ValueError('Mirror FACE plane anchored BODY has no unique explicit same-asset stored-ID join')
            mapping,binding=choices[0]
            blob_member=mapping['history_blob_member'];blob=members[blob_member]
            parsed=inspect_asm(blob)
            tags=decode_asm_generic_tags(blob,parsed=parsed,allow_fpm_tracking=True)
            topology=decode_topology(parsed)
            if tags['unresolved'] or topology['unresolved']:
                raise ValueError('Mirror FACE plane requires complete initial generic naming and reciprocal topology')
            matches=match_recipe_tag_names(recipe,tags,parsed=parsed)
            entry=matches['name_entries'][0]
            face_matches=[c for c in entry['candidates'] if c['owner_kind']=='face'
                and c['body_graph_membership']==[binding['asm_body_index']]]
            if len(face_matches)!=1:
                raise ValueError('Mirror FACE plane complete name is missing or ambiguous in the mapped BODY FACE namespace')
            match=face_matches[0]
            operand=_face_cache(topology,binding['asm_body_index'],match['owner_record_index'])
            operand['scope']='Named initial Mirror support FACE cache with identity BODY transform; no temporal or API topology assignment'
            surface=operand['surface']
            if surface['kind']!='plane-surface' or surface.get('analytic_surface',{}).get('kind')!='Plane':
                raise ValueError('Mirror FACE plane selected stored surface is not an explicit typed plane')
            origin,normal,axis=surface['raw_origin'],surface['normal'],surface['stored_reference_axis']
            if any(not math.isfinite(v) for v in origin+normal+axis):
                raise ValueError('Mirror FACE plane stored frame is not finite')
            norm=math.hypot(*normal);axis_norm=math.hypot(*axis)
            if not math.isfinite(norm) or not math.isfinite(axis_norm) or norm<=0 or axis_norm<=0:
                raise ValueError('Mirror FACE plane stored frame lengths are not finite and positive')
            unit=[v/norm for v in normal]
            normalized_axis=[v/axis_norm for v in axis]
            if abs(sum(a*b for a,b in zip(normalized_axis,unit)))>1e-10:
                raise ValueError('Mirror FACE plane normal/reference frame is degenerate or nonorthogonal')
            plane_offset=-sum(n*p for n,p in zip(unit,origin))
            if not math.isfinite(plane_offset):
                raise ValueError('Mirror FACE plane derived offset is not finite')
            points=[p['raw_origin'] for edge in operand['boundary_edges'] for p in edge['points']]
            if (len(operand['boundary_edges'])!=4 or len({r['loop_record_index'] for r in operand['incidence_routes']})!=1
                    or any(e['curve']['kind']!='straight-curve' for e in operand['boundary_edges'])
                    or any(not math.isfinite(v) for point in points for v in point)):
                raise ValueError('Mirror FACE plane captured four-Line boundary is incomplete or nonfinite')
            residuals=[abs(sum(n*(p-o) for n,p,o in zip(unit,point,origin))) for point in points]
            if any(not math.isfinite(r) for r in residuals) or max(residuals)>1e-9:
                raise ValueError('Mirror FACE plane identity-fixed boundary points disagree with stored plane')
            selected_tag=next(t for t in tags['tags'] if t['attribute_record_index']==match['attribute_record_index'])
            attr=parsed['records'][match['attribute_record_index']]
            record_ids=[r.object_id for r in (rec,control_record,proxy_record,descriptor_record,recipe_record,context_record,
                helper_record,support_record,support_source_record,anchor_record,native_body_record,anchor_owner_record)]
            result['decoded'].append(dict(feature_object_id=owner,plane_selection_record_object_id=proxy_id,
                descriptor_object_id=ids[0],recipe=recipe,exact_recipe_payload_replay=True,
                native_plane_source=owned,support_provenance=dict(support_object_id=support_id,
                    support_source_record_object_ids=[support_source_id],historical_body_anchor_object_id=anchor['object_id'],
                    historical_anchor_source_owner_object_id=anchor['source_owner_object_id'],
                    support_contains_anchor_owner=support_source_id==anchor['source_owner_object_id'],
                    stored_support_cache_bytes_hex=[support[23:31].hex(),support[42:50].hex()],
                    role_scope='Literal support source and historical anchor owner retained independently; no global identity equivalence'),
                native_record_proof=[raw(typed(i)[0]) for i in dict.fromkeys(record_ids)],
                mapping_record_object_id=mapping['mapping_record_object_id'],mapping_owner_object_id=mapping['owner_object_id'],
                history_blob_member=blob_member,source_body_binding=binding,
                complete_name_match=entry,mapped_body_FACE_candidates=face_matches,selected_generic_tag=selected_tag,
                selected_attribute_original_bytes=dict(record_index=attr['index'],offset=attr['offset'],end_offset=attr['end_offset'],
                    payload_hex=blob[attr['offset']:attr['end_offset']].hex()),
                cached_operand=operand,cache_plane=dict(kind='Plane',raw_origin=origin,raw_normal=normal,
                    normalized_unit_normal=unit,normalized_plane_equation=unit+[plane_offset],
                    stored_reference_axis=axis,stored_is_v_reversed=surface['is_v_reversed'],
                    stored_u_interval=surface['u_interval'],stored_v_interval=surface['v_interval'],
                    face_is_reversed=operand['face']['is_reversed'],
                    derived_maximum_boundary_plane_residual_raw=max(residuals),
                    coordinate_scope='Raw explicitly mapped initial ASM cache, identity BODY transform; no occurrence/world transform inferred'),
                API_handle_identity=None,persistent_source_identity=None,current_source_identity=None,
                qualified_historical_state=None,reflection_geometry=None,scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
            result['unresolved'].append(dict(feature_object_id=owner,class_guid=MIRROR,reason=str(error)))
    return result
