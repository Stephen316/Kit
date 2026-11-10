"""Bounded empty-child, VERTEX generic-name and FACE FPM attribute evidence."""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags,match_recipe_tag_names
from decode_counted_asm_names import decode_counted_asm_name
from decode_brep import decode_topology
from decode_pcurve_variants import encode_pcurve_fields
from fusion_archive import read_members

FILES=(
    *('circularmodes-45f859c1f1b6/feature_'+x+'.f3d' for x in ('adjust','identical','optimized')),
    *('mirrorfeatures-1ffa1b15c612/feature_'+x+'.f3d' for x in ('adjust','identical','optimized')),
    *('moretools-88a2cd6cad0b/'+x+'.f3d' for x in ('MoveRotate','MoveTranslate')),
    *('movemodes-0dd2f72dd9a7/'+x+'.f3d' for x in ('point_to_position_component','point_to_position_nested_design')),
    *('movemodes-34cba3ced135/'+x+'.f3d' for x in ('along_axis','along_sketch_line','free','point_to_point','point_to_position','rotate_axis','xyz_component','xyz_design','xyz_nested_design')),
    *('rectmodes-a069f8f4b8a2/feature_'+x+'.f3d' for x in ('adjust','identical','optimized')),
    'rectsymholdouts-cf85ce4a0382/feature_input.f3d','remainingbodyinputs-7b3357274e85/mirror_two_features.f3d',
    'specialfillets-a279c7bccbd1/full_explicit_swapped.f3d','specialfillets-d50f7a4f04e0/full_automatic.f3d',
    'specialfillets-d50f7a4f04e0/full_explicit.f3d','splinepatches-900d152c2380/splinepatches.f3d',
    'splinepatches-ac5e846e59c0/splinepatches.f3d',
    *('surfacebounds-ac801bb00fae/untrim_'+x+'.f3d' for x in ('all','external','internal','manual')),
    'surfacetools-856ca50cf4c7/reverse_normal.f3d')


def _owner_chain(records,owner_id,attribute_id,limit):
    owner=records[owner_id];current=owner['tokens'][0]['value'];previous=-1;chain=[]
    while current!=-1:
        if current in chain or not 0<=current<limit or len(chain)>=128:
            raise ValueError('Variant owner attribute chain cyclic/outside initial geometry')
        record=records[current];ts=record['tokens']
        if (record['name']!='ATTRIB_CUSTOM-attrib' or len(ts)<6 or ts[1]['kind']!='integer' or ts[1]['value']!=-1
                or any(ts[i]['kind']!='pointer' for i in (0,2,3,4))
                or ts[4]['value']!=owner_id or ts[3]['value']!=previous):
            raise ValueError('Variant attribute chain owner/previous pointers disagree')
        chain.append(current);previous,current=current,ts[2]['value']
    if attribute_id not in chain:raise ValueError('Variant attribute absent from explicit owner chain')
    return chain


def validate(zstd_library,root=None):
    root=Path(root) if root is not None else Path(__file__).resolve().parent
    report=dict(scope='All216 observed initial-geometry empty-child/VERTEX-generic/FACE-FPM variants in34saved files; exact payload framing and reciprocal owners, no native/persistent identity inference',
        shared_interfaces={
            'payload':'decode_counted_asm_name(record,*,allow_empty_names=False); opt-in empty term name only after typed child validation',
            'owner_reader':'decode_asm_generic_tags(blob,parsed=None,*,allow_fpm_tracking=False)',
            'nested_scope':'Empty-name children are ignored validated metadata, never topology tags or naming-match candidates',
            'vertex_match_scope':'Match candidates use actual typed VERTEX membership in body_graph.vertex_indices, not edge_indices'},
        observed_grammar={
            'empty_child':'Exactly17tokens; pointer[-1],integer[-1],next/previous pointers[-1,-1],parent custom-attribute owner pointer; generic definition/schema3,3,-1/namespace; one term: explicitname length0,string empty,index0,componentcount1,positive signed32 component,zero terminator. Parent field0 points to this child; parent topology owner is BODY or FACE.',
            'vertex_generic':'Existing counted generic schema with one nonempty decimal name,index0,one positive component and zero terminator. Typed VERTEX attribute head/sibling chain reciprocates every owner.',
            'FACE_FPM':'Exactly8tokens, standard custom attribute header, FPM_tracked_attrib_def,integer schema1,positive uint32-range integer literal. Typed FACE attribute chain reciprocates owner; value remains an unqualified tracking literal.'},
        samples=[],guards=[],prior_dictionary_controls=[],limitations=[
            'Empty term names are observed only in the exact singleton child metadata layout. They do not add an unnamed topology candidate or establish a native object ID.',
            'Generic naming tuple matches establish serialized correspondence only; duplicates are retained. The synthetic tuple probes below are validator controls, not captured native selection recipes.',
            'FPM values remain literal uint32-range integers; neither matching a feature ID numerically nor repeating across faces establishes feature ownership or historical state.',
            'Header-child links, sibling links, topology pointers and native Design object IDs remain distinct explicit namespaces.',
            'Occurrence counts refer to the saved34-file frontier subset, not a complete-format coverage claim.'])
    totals=Counter();empty_values=Counter();vertex_values=Counter();fpm_values=Counter();parents=Counter();saved={};contexts={}
    for filename in FILES:
        members=read_members(root/filename,zstd_library)
        for member,blob in members.items():
            if not member.endswith(('.smb','.smbh')):continue
            parsed=inspect_asm(blob);rr=parsed['records'];limit=next((r['index'] for r in rr if r['record_kind']=='marker'),len(rr))
            target=[]
            for r in rr[:limit]:
                ts=r['tokens']
                if r['name']!='ATTRIB_CUSTOM-attrib' or len(ts)<=5 or ts[4]['kind']!='pointer' or not 0<=ts[4]['value']<limit:continue
                owner=rr[ts[4]['value']]
                if ts[5]['value']=='generic_tag_attrib_def' and any(t['kind']=='string' and t['value']=='' for t in ts[6:]):family='empty_child'
                elif ts[5]['value']=='generic_tag_attrib_def' and owner['name']=='vertex':family='vertex_generic'
                elif ts[5]['value']=='FPM_tracked_attrib_def' and owner['name']=='face':family='FACE_FPM'
                else:continue
                target.append((family,r,owner))
            if not target:continue
            summary=decode_asm_generic_tags(blob,parsed,allow_fpm_tracking=True)
            tags={r['attribute_record_index']:r for r in summary['tags']}
            ignored={r['attribute_record_index']:r for r in summary['ignored_validated_other_definition_attributes']}
            row=dict(file=filename,member=member,blob_sha256=hashlib.sha256(blob).hexdigest(),variants=[],
                     remaining_unrelated_errors=summary['unresolved'])
            contexts[(filename,member)]=(blob,parsed,summary)
            for family,r,owner in target:
                ts=r['tokens'];attribute=r['index'];owner_id=owner['index']
                first,second=r['name'].split('-')
                raw=b'\x0e'+bytes([len(first)])+first.encode()+b'\x0d'+bytes([len(second)])+second.encode()+encode_pcurve_fields(ts)+b'\x11'
                assert raw==blob[r['offset']:r['end_offset']]
                totals[family]+=1;totals['complete_record_byte_replays']+=1
                entry=dict(family=family,attribute_record_index=attribute,owner_record_index=owner_id,owner_kind=owner['name'],
                           complete_record_byte_replay_matches=True,complete_record_sha256=hashlib.sha256(raw).hexdigest())
                if family=='empty_child':
                    assert len(ts)==17 and [ts[i]['value'] for i in (0,1,2,3)]==[-1]*4
                    assert owner['name']=='ATTRIB_CUSTOM-attrib' and owner['tokens'][0]['kind']=='pointer' and owner['tokens'][0]['value']==attribute
                    topology_owner=rr[owner['tokens'][4]['value']]
                    assert topology_owner['name'] in ('body','face')
                    topchain=_owner_chain(rr,topology_owner['index'],owner_id,limit)
                    childchain=_owner_chain(rr,owner_id,attribute,limit)
                    assert childchain==[attribute]
                    payload=decode_counted_asm_name(r,allow_empty_names=True)
                    term,=payload['terms']
                    assert payload['stored_term_count']==1 and term['name']=='' and term['stored_index']==0
                    assert term['stored_reference_component_count']==1 and 1<=term['stored_reference_components_int32'][0]<=0x7fffffff
                    assert bytes.fromhex(payload['payload_hex'])==blob[payload['payload_offset']:payload['payload_end_offset']]
                    assert attribute not in tags and attribute in ignored and ignored[attribute]['owner_kind']=='ATTRIB_CUSTOM-attrib'
                    assert ignored[attribute]['owner_record_index']==owner_id
                    empty_values[term['stored_reference_components_int32'][0]]+=1;parents[topology_owner['name']]+=1
                    entry.update(payload=payload,validated_child_metadata=ignored[attribute],child_owner_attribute_chain=childchain,
                                 parent_topology_attribute_chain=topchain,topology_owner_record_index=topology_owner['index'],topology_owner_kind=topology_owner['name'])
                    # A deliberately synthetic empty tuple must never become a
                    # topology candidate through the metadata branch.
                    if not summary['unresolved']:
                        probe=dict(object_id=None,payload_kind='SyntheticEmptyTupleValidatorProbe',name_table=[dict(table_index=0,terms=payload['terms'])])
                        match=match_recipe_tag_names(probe,summary,parsed=parsed)
                        assert match['name_entries'][0]['candidate_count']==0
                        entry['synthetic_empty_tuple_has_no_topology_candidates']=True
                elif family=='vertex_generic':
                    chain=_owner_chain(rr,owner_id,attribute,limit)
                    payload=decode_counted_asm_name(r);term,=payload['terms']
                    assert len(ts)==17 and payload['stored_term_count']==1 and term['name'].isdecimal() and term['stored_index']==0
                    assert term['stored_reference_component_count']==1
                    assert attribute in tags and tags[attribute]['owner_kind']=='vertex' and tags[attribute]['owner_attribute_chain']==chain
                    first_edge=owner['tokens'][3]['value'];point=owner['tokens'][5]['value']
                    assert owner['tokens'][3]['kind']=='pointer' and rr[first_edge]['name']=='edge'
                    assert owner['tokens'][5]['kind']=='pointer' and rr[point]['name']=='point'
                    assert owner_id in (rr[first_edge]['tokens'][3]['value'],rr[first_edge]['tokens'][5]['value'])
                    assert not summary['unresolved'],summary['unresolved']
                    probe=dict(object_id=None,payload_kind='SyntheticVertexTupleValidatorProbe',name_table=[dict(table_index=0,terms=payload['terms'])])
                    match=match_recipe_tag_names(probe,summary,parsed=parsed);candidates=match['name_entries'][0]['candidates']
                    own=next(c for c in candidates if c['attribute_record_index']==attribute)
                    topology=decode_topology(parsed)
                    expected=[g['body_index'] for g in topology['body_graphs'] if owner_id in g['vertex_indices']]
                    assert own['owner_kind']=='vertex' and own['body_graph_membership']==expected and expected
                    vertex_values[term['stored_reference_components_int32'][0]]+=1
                    entry.update(payload=payload,owner_attribute_chain=chain,explicit_incident_edge_record_index=first_edge,
                                 explicit_point_record_index=point,synthetic_tuple_probe_candidates=candidates,
                                 candidate_BODY_membership_matches_vertex_graph=True)
                else:
                    chain=_owner_chain(rr,owner_id,attribute,limit)
                    assert len(ts)==8 and ts[6]['kind']=='integer' and ts[6]['value']==1
                    literal=ts[7]['value'];assert ts[7]['kind']=='integer' and 1<=literal<=0xffffffff
                    assert attribute in ignored and ignored[attribute]['owner_kind']=='face' and ignored[attribute]['stored_tracking_literal']==literal
                    assert attribute not in tags
                    fpm_values[literal]+=1
                    entry.update(owner_attribute_chain=chain,stored_tracking_literal=literal,
                                 identity_interpretation=None,validated_other_metadata=ignored[attribute])
                row['variants'].append(entry);saved.setdefault(family,(blob,parsed,r,summary))
            report['samples'].append(row)
    assert (totals['empty_child'],totals['vertex_generic'],totals['FACE_FPM'])==(90,48,78)
    report['observed_distributions']=dict(empty_child_components=dict(sorted(empty_values.items())),
        empty_child_parent_topology_kinds=dict(parents),vertex_generic_components=dict(sorted(vertex_values.items())),FACE_FPM_literals=dict(sorted(fpm_values.items())))
    def reject(label,action):
        try:action()
        except (ValueError,IndexError,KeyError) as e:report['guards'].append(dict(label=label,rejected=True,reason=str(e)))
        else:raise AssertionError(label+' accepted')
    blob,parsed,child,summary=saved['empty_child']
    reject('Default payload helper rejects empty topology name',lambda:decode_counted_asm_name(child))
    for label,index,value in [('Empty child name byte length mismatch',11,1),('Invalid counted component count',14,4),('Nonzero counted term terminator',16,1)]:
        changed=copy.deepcopy(child);changed['tokens'][index]['value']=value
        reject(label,lambda changed=changed:decode_counted_asm_name(changed,allow_empty_names=True))
    for label,index,value in [('Wrong parent backlink',4,0),('Nonzero child stored index',13,1),('Unexpected nonempty child name',12,'x'),('Negative singleton child component',15,-1)]:
        changed=copy.deepcopy(parsed);changed['records'][child['index']]['tokens'][index]['value']=value
        out=decode_asm_generic_tags(blob,changed,allow_fpm_tracking=True)
        assert any(r['attribute_record_index']==child['index'] for r in out['unresolved'])
        assert all(r['attribute_record_index']!=child['index'] for r in out['tags'])
        report['guards'].append(dict(label=label,rejected=True,reason=next(r['reason'] for r in out['unresolved'] if r['attribute_record_index']==child['index'])))
    for family,label,index,value in [('vertex_generic','Vertex generic owner pointer disagrees with chain',4,0),
                                    ('FACE_FPM','FACE FPM schema differs from captured1',6,2)]:
        raw,source,record,_=saved[family]
        changed=copy.deepcopy(source);changed['records'][record['index']]['tokens'][index]['value']=value
        out=decode_asm_generic_tags(raw,changed,allow_fpm_tracking=True)
        assert any(r['attribute_record_index']==record['index'] for r in out['unresolved'])
        report['guards'].append(dict(label=label,rejected=True,
            reason=next(r['reason'] for r in out['unresolved'] if r['attribute_record_index']==record['index'])))
    # Prior exact catalogs are independent saved controls, not a freshly
    # regenerated expected dictionary from the same parser implementation.
    golden=json.loads((root/'asm-recipe-tag-decoding.json').read_text())
    for sample in golden['samples'][:2]:
        member=sample['expected_pipe_evidence']['history_blob_member'];raw=read_members(root/sample['file'],zstd_library)[member]
        actual=decode_asm_generic_tags(raw,allow_fpm_tracking=True)
        assert actual==sample['expected_tag_catalog']
        report['prior_dictionary_controls'].append(dict(file=sample['file'],member=member,complete_prior_dictionary_unchanged=True))
    report['validation']=dict(totals,saved_files=len(FILES),target_blob_count=len(contexts),guards_passed=len(report['guards']),
        prior_dictionary_controls=len(report['prior_dictionary_controls']),native_feature_ID_claims=0,new_live_API_calls=0,
        child_topology_tags_emitted=0,vertex_candidate_membership_checks=totals['vertex_generic'])
    return report
