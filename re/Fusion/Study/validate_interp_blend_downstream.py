"""Independent native provenance behind three geometry-enabled downstream changes.

Calls only the focused readers; no decode_basics/main invocation or live Fusion.
"""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags,match_recipe_tag_names
from decode_basics import decode_sketches
from decode_body_bindings import decode_body_bindings
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections
from decode_brep import decode_topology
from decode_parameters import read_string
from decode_placement import decode_placement
from decode_profile_cache_correspondence import decode_profile_cache_correspondence
from decode_profiles import read_loops
from decode_recipe_components import decode_counted_recipe
from decode_selection_recipe_incidence import decode_selection_recipe_incidence
from decode_selection_context_recipes import TOPOLOGY
from decode_sketch import attributes,reference
from decode_sketch_attributes import decode_sketch_attribute
from validate_mesh_remesh import load

FILES=tuple('variablefillets-a5080b076434/'+f+'.f3d' for f in ('one_quarter','one_three_quarters','two_intermediates'))


def validate(root,zstd):
    samples=[];checks=[];guards=[];first=None
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    geometry=json.loads((root/'interp-blend-cache-decoding.json').read_text())
    for archive in FILES:
        data,records,features,member,members=load(root,archive,zstd)
        decode_sketches(data,records,features);decode_placement(data,records,features);before=copy.deepcopy(features)
        selections=decode_body_selections(data,records)
        bindings=decode_body_bindings(data,records,member,{'streams':[{'member':n} for n in members if n.endswith('.smbh')]})
        identifiers=decode_body_asm_identifiers(data,records,member,members,bindings)
        profiles=decode_profile_cache_correspondence(data,records,features,member,members,identifiers)
        incidence=decode_selection_recipe_incidence(data,records,features,member,members,identifiers,selections)
        check(archive+' unique recovered profile row, no unresolved',len(profiles['decoded'])==1 and not profiles['unresolved'])
        row=profiles['decoded'][0];owner=row['source_feature_object_id']
        check(archive+' source Extrude remains243',owner==243 and row['source_feature_kind']=='Extrude')
        primary={r.object_id:r for r in records if r.is_primary}
        def body(identity):
            r=primary[identity];return data[r.body:r.end]
        descriptor=primary[row['profile_descriptor_object_id']]
        check(archive+' typed owned profile descriptor',descriptor.class_guid=='4BD53E5A-0B3E-45E5-AE8B-02044306485A' and reference(body(descriptor.object_id),len(body(descriptor.object_id))-11)==owner)
        namespace,end=read_string(body(descriptor.object_id),17);sketch_text,end=read_string(body(descriptor.object_id),end)
        sketch=next(f for f in features if f.get('sketch_object_id')==row['native_sketch_object_id'])
        check(archive+' explicit descriptor sketch namespace and loop ownership',namespace==row['namespace_text'] and int(sketch_text)==sketch['sketch_object_id'] and reference(body(descriptor.object_id),2)==row['profile_loop_definition_object_id'] and read_loops(body(row['profile_loop_definition_object_id']),descriptor.object_id,sketch)==row['profile_loops'])
        source_lines={c['object_id']:c for c in sketch['geometry'] if c['kind']=='Line'}
        source_degrees=Counter()
        for source in row['source_curves']:
            native=body(source['native_entity_object_id']);props,_=attributes(native,2);curve=source_lines[source['native_entity_object_id']]
            check(archive+' owned native primary tag'+str(curve['object_id']),reference(native,len(native)-11)==row['native_sketch_object_id'] and props['crv_primary_id']==source['native_entity_tag'] and props['crv_secondary_id']==0)
            source_degrees.update((curve['start_point_id'],curve['end_point_id']))
        check(archive+' four wholeLines form closed undirected endpoint cycle',len(row['source_curves'])==4 and len(source_degrees)==4 and set(source_degrees.values())=={2})
        anchor=next(a for a in selections['body_anchors'] if a['object_id']==row['body_anchor_object_id'])
        check(archive+' explicit source-owner BODY anchor',anchor['source_owner_object_id']==owner and anchor['native_body_object_id']==row['native_body_object_id'])
        mapping=next(m for m in identifiers['decoded'] if m['mapping_record_object_id']==row['mapping_record_object_id']);binding=next(b for b in mapping['bindings'] if b['native_body_object_id']==row['native_body_object_id'])
        blob=members[row['history_blob_member']];parsed=inspect_asm(blob);topology=decode_topology(parsed);nodes={n['index']:n for n in topology['nodes']}
        check(archive+' complete sameasset typed BODY identity and geometry',not topology['unresolved'] and parsed['records'][binding['asm_body_index']]['name']=='body' and parsed['records'][binding['asm_body_index']]['tokens'][1]['value']==binding['stored_handle']==row['asm_stored_body_entity_id'])
        graph=next(g for g in topology['body_graphs'] if g['body_index']==row['asm_body_index'])
        expected=next(s for s in geometry['samples'] if s['archive']==archive)
        check(archive+' newly decoded surface exactly focused geometry proof',json.loads(json.dumps(nodes[10]['bspline_surface']))==expected['expected_cache'])
        tags=decode_asm_generic_tags(blob,parsed,allow_fpm_tracking=True)
        validated={a['attribute_record_index']:a for a in tags['ignored_validated_other_definition_attributes'] if a['definition_name']=='sketch_attrib_def'}
        native_coedge_proof=[]
        for source in row['source_curves']:
            check(archive+' every tag retains two candidates'+str(source['native_entity_tag']),len(source['cached_coedge_candidates'])==2)
            for candidate in source['cached_coedge_candidates']:
                attribute=parsed['records'][candidate['attribute_record_index']];payload=decode_sketch_attribute(attribute);qualified=validated[attribute['index']]
                check(archive+' payload actualbyte replay'+str(attribute['index']),bytes.fromhex(payload['payload_hex'])==blob[payload['payload_offset']:payload['payload_end_offset']])
                coedge=nodes[candidate['coedge_record_index']];loop=nodes[coedge['loop_index']];face=nodes[loop['face_index']];edge=nodes[coedge['edge_index']]
                check(archive+' qualified typed owner and reciprocal incidence'+str(coedge['index']),qualified['owner_kind']=='coedge' and qualified['owner_record_index']==coedge['index'] and coedge['index'] in graph['coedge_indices'] and edge['index'] in graph['edge_indices'] and face['index'] in graph['face_indices'] and nodes[coedge['next_coedge_index']]['previous_coedge_index']==coedge['index'] and nodes[coedge['previous_coedge_index']]['next_coedge_index']==coedge['index'])
                check(archive+' only canonical firstfield/tag match after ownership'+str(coedge['index']),payload['stored_decimal_text_fields']==[str(source['native_entity_tag']),'0','0','0','1','1'])
                native_coedge_proof.append(dict(native_entity_object_id=source['native_entity_object_id'],native_entity_tag=source['native_entity_tag'],attribute_record_index=attribute['index'],coedge_record_index=coedge['index'],edge_record_index=edge['index'],loop_record_index=loop['index'],face_record_index=face['index'],payload_replay_sha256=hashlib.sha256(bytes.fromhex(payload['payload_hex'])).hexdigest()))
        check(archive+' no source edge identity falsely resolved',not incidence['associations'] and len(incidence['unresolved'])==1 and incidence['unresolved'][0]['descriptor_object_id']==302)
        detail=incidence['unresolved'][0]['bounded_operand_evidence'];descriptor=primary[302];descriptor_payload=body(302)
        check(archive+' original source descriptor and recipe route',descriptor.class_guid==TOPOLOGY and reference(descriptor_payload,4)==detail['recipe_object_id'])
        recipe=decode_counted_recipe(data,primary[detail['recipe_object_id']]);correspondence=match_recipe_tag_names(recipe,tags,parsed=parsed)
        named={r['name_table_index']:r for r in correspondence['name_entries']}
        for operand in detail['named_face_operands']:
            entry=named[operand['name_table_index']]
            check(archive+' complete named-face tuple and graph owner'+str(operand['face_record_index']),entry['candidate_count']==1 and entry['candidates'][0]['owner_kind']=='face' and entry['candidates'][0]['owner_record_index']==operand['face_record_index'] and entry['candidates'][0]['attribute_record_index']==operand['attribute_record_index'] and entry['candidates'][0]['body_graph_membership']==[row['asm_body_index']])
        edge_faces={}
        for coedge_id in graph['coedge_indices']:
            coedge=nodes[coedge_id];loop=nodes[coedge['loop_index']]
            edge_faces.setdefault(coedge['edge_index'],set()).add(loop['face_index'])
        needed={f['face_record_index'] for f in detail['named_face_operands']}
        candidates=[e for e,faces in edge_faces.items() if faces==needed]
        check(archive+' exhaustive explicit mapped-body incidence has zero edges',len(needed)==2 and candidates==[] and detail['initial_incidence_candidate_record_indices']==[])
        check(archive+' unresolved status accurately preserves historical ambiguity',incidence['unresolved'][0]['reason']=='Named source operands do not identify exactly one surviving initial-cache entity; historical state replay unresolved' and detail['native_body_object_id']==row['native_body_object_id'] and detail['explicit_asm_body_index']==row['asm_body_index'])
        check(archive+' direct readers did not attach or mutate features',features==before)
        samples.append(dict(archive=archive,expected_profile_cache_correspondences=profiles,expected_selection_recipe_incidence=incidence,
            profile_feature_object_id=owner,expected_profile_feature_attachment=[row],
            independent_native_proof=dict(source_profile_descriptor_object_id=row['profile_descriptor_object_id'],source_loop_definition_object_id=row['profile_loop_definition_object_id'],source_sketch_object_id=row['native_sketch_object_id'],source_undirected_point_degrees=dict(source_degrees),native_source_anchor=anchor,sameasset_BODY_binding=binding,
                complete_coedge_attribute_correspondences=native_coedge_proof,recipe_object_id=recipe['object_id'],recipe_payload_hex=recipe['payload_hex'],complete_name_correspondence=correspondence,
                named_source_face_operands=detail['named_face_operands'],all_mapped_BODY_edge_incident_faces=[dict(edge_record_index=e,face_record_indices=sorted(fs)) for e,fs in sorted(edge_faces.items())],surviving_named_pair_edge_record_indices=candidates,
                selected_edge_identity=None,current_or_historical_lifecycle=None),
            explanation='New surface cache removes the global incomplete-topology gate. The preexisting owned profile/Sketch/tag and explicit source-owner BODY/blob routes now qualify eight COEDGE naming candidates. The separate source edge recipe still has no surviving edge with its complete named-face pair; it remains unresolved with more precise evidence, without choosing geometry or replaying history.'))
        if first is None:first=(data,records,features,member,members,identifiers,row)
    # Two bounded ownership guards: these naming correspondences cannot survive broken native routes.
    data,records,features,member,members,identifiers,row=first
    for label,identity,offset,value in (
        ('Reject profile descriptor owner mismatch',row['profile_descriptor_object_id'],-10,row['source_feature_object_id']+1),
        ('Reject native profile curve Sketch owner mismatch',row['source_curves'][0]['native_entity_object_id'],-10,row['native_sketch_object_id']+1)):
        r=next(r for r in records if r.is_primary and r.object_id==identity);changed=bytearray(data);struct.pack_into('<Q',changed,r.end+offset,value)
        result=decode_profile_cache_correspondence(bytes(changed),records,features,member,members,identifiers)
        check(label,not result['decoded'] and len(result['unresolved'])==1)
        guards.append(dict(guard=label,expected_unresolved=result['unresolved']))
    files=('validate_interp_blend_downstream.py','decode_profile_cache_correspondence.py','decode_selection_recipe_incidence.py','decode_interp_blend_cache.py','decode_body_bindings.py','decode_body_asm_identifiers.py','decode_asm_recipe_tags.py')
    return dict(scope='Focused direct-reader downstream proof for three newly evaluable interpolation-width surface caches; native identities precede naming/incidence, no maincache-derived expected output',sample_count=3,profile_feature_count=3,profile_source_curve_count=12,COEDGE_candidate_count=24,unresolved_source_recipe_count=3,
        check_count=len(checks),malformed_guard_count=len(guards),samples=samples,checks=checks,malformed_guards=guards,
        geometry_proof_report='interp-blend-cache-decoding.json',geometry_proof_report_sha256=hashlib.sha256((root/'interp-blend-cache-decoding.json').read_bytes()).hexdigest(),
        source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files},
        limitations=['Full expected summaries are independently produced by focused profile/incidence readers plus typed native/ASM validation, never taken from cached main outputs',
            'All multiple COEDGE candidates remain; no uniquely selected edge, API handle, lifecycle or persistent topology identity inferred',
            'Zero surviving source-incidence candidates preserves unresolved historical-state interpretation; newly evaluable geometry does not reconstruct removed edges',
            'No production edits, live API/UI, mainreader invocation or wholecorpus rerun'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--zstd-library');p.add_argument('--output',default='interp-blend-downstream-decoding.json');a=p.parse_args();root=Path(__file__).resolve().parent
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    r=validate(root,z);Path(a.output).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('sample_count','check_count','malformed_guard_count','COEDGE_candidate_count')}))
if __name__=='__main__':main()
