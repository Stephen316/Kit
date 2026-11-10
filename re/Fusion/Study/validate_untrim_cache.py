"""Focused Untrim literal cache-view and opt-in naming-version evidence."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_asm_history import decode_asm_history
from decode_asm_name_versions import decode_asm_name_versions
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_bindings import decode_body_bindings
from decode_brep import decode_topology
from decode_recipe_components import decode_counted_recipe
from decode_sketch import reference
from fusion_archive import read_members
from fusion_metadata import design_records
from materialize_untrim_cache import materialize_untrim_cache, SCOPE, COUNTS

ROOT=Path(__file__).resolve().parent
FILES=tuple('surfacebounds-ac801bb00fae/untrim_'+name+'.f3d' for name in ('manual','internal','external','all'))


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate(zstd):
    checks=[];guards=[];samples=[];old_defaults=[];view_fixture=None;modified_fixture=None
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    for filename in FILES:
        members=read_members(ROOT/filename,zstd)
        member=next(n for n in members if n.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
        data=members[member];records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        primary={r.object_id:r for r in records if r.is_primary}
        minimal=dict(streams=[dict(member=n,complete_token_stream=True,declared_root_records=[])
            for n in members if n.endswith('.smbh')])
        native=decode_body_bindings(data,records,member,minimal)
        mapped=decode_body_asm_identifiers(data,records,member,members,native)
        check(filename+' fresh typed native BODY map',not mapped['unresolved'] and len(mapped['decoded'])==1)
        mapping=mapped['decoded'][0]
        check(filename+' singleton native source BODY',mapping['body_count']==1 and len(mapping['bindings'])==1)
        binding=mapping['bindings'][0];blob_member=mapping['history_blob_member'];blob=members[blob_member]
        parsed=inspect_asm(blob);before=copy.deepcopy(parsed);history=decode_asm_history(blob,parsed=parsed)
        initial_topology=decode_topology(parsed);initial_tags=decode_asm_generic_tags(blob,parsed,allow_fpm_tracking=True)
        default=decode_asm_name_versions(blob,parsed=parsed)
        optin=decode_asm_name_versions(blob,parsed=parsed,allow_modified_nested=True)
        check(filename+' bounded modified nested proof',len(optin['decoded'])==1 and not optin['unresolved'])
        version=optin['decoded'][0]
        check(filename+' version belongs to native mapped initial BODY',version['initial_body_record_index']==binding['asm_body_index'])
        check(filename+' full nested child retained',version['initial_attribute']['validated_nested_metadata']['exact_full_payload_replay'])
        modified=filename.endswith(('/untrim_external.f3d','/untrim_all.f3d'))
        if modified:
            check(filename+' default unchanged explicit rejection',not default['decoded'] and default['unresolved']==[
                {'reason':'Naming-version nested-child family requires identical complete paired tuples'}])
            a,b=version['initial_attribute']['terms'],version['trailing_attribute']['terms']
            check(filename+' complete two/one nested tuples',[t['stored_reference_components_int32'] for t in a]==[[301,-302]]
                and [t['stored_reference_components_int32'] for t in b]==[[301]])
            if modified_fixture is None:modified_fixture=(blob,parsed,version)
        else:check(filename+' already supported name-version output exact',default==optin)
        base=dict(archive=filename,archive_sha256=sha(ROOT/filename),member=blob_member,
            blob_sha256=hashlib.sha256(blob).hexdigest(),native_source_mapping=mapping,
            expected_name_versions_default=default,expected_name_versions_opt_in=optin)
        if modified:
            try:materialize_untrim_cache(blob,initial_body_record_index=binding['asm_body_index'],stored_body_identifier=binding['stored_handle'])
            except ValueError as error:base['materializer_rejection']=str(error)
            else:raise AssertionError('Six-state cache admitted as five-state view')
            check(filename+' six-state view explicitly rejected',base['materializer_rejection']=='Untrim cache view is outside the observed five-state journal family')
        else:
            view=materialize_untrim_cache(blob,initial_body_record_index=binding['asm_body_index'],stored_body_identifier=binding['stored_handle'],parsed=parsed,history=history)
            check(filename+' literal complete history preserved',view['canonical_history']==history and history['neighbor_chain']==[0,2,4,3,1])
            check(filename+' qualified BODY uses exact native stored identifier',view['stored_body_identifier']==binding['stored_handle']
                and view['initial_body_record_index']==binding['asm_body_index'] and view['qualified_dangling_pointer_count']==0)
            origins={r['view_record_index']:r for r in view['origin_map']}
            table=history['geometry_entities'];entities=[parsed['records'][r['inspection_record_index']] for r in table]
            aliases={r['side1_entity_ordinal']:r['side0_entity_ordinal'] for r in view['literal_pair_aliases']}
            chosen=view['selected_geometry_entity_ordinals'];dense={v:i for i,v in enumerate(chosen)}
            check(filename+' typed paired BODY origin',origins[view['qualified_body_view_record_index']]==view['qualified_body_origin']
                and aliases[view['initial_body_geometry_ordinal']]==view['qualified_body_origin']['geometry_entity_ordinal'])
            for r in view['view_parsed']['records']:
                origin=origins[r['index']];original=entities[origin['geometry_entity_ordinal']]
                expected=copy.deepcopy(original);expected['index']=r['index'];expected['section']='geometry'
                for token in expected['tokens']:
                    if token['tag']==12 and token['value']!=-1:token['value']=dense[aliases.get(token['value'],token['value'])]
                check(filename+' exact literal pointer-only view record'+str(r['index']),r==expected)
            for rewrite in view['rewritten_pointer_evidence']:
                off=rewrite['token_offset']
                check(filename+' raw pointer replay at'+str(off),blob[off]==12
                    and struct.unpack_from('<q',blob,off+1)[0]==rewrite['stored_target_geometry_entity_ordinal'])
            topology=view['topology'];nodes={n['index']:n for n in topology['nodes']}
            graph=next(g for g in topology['body_graphs'] if g['body_index']==view['qualified_body_view_record_index'])
            check(filename+' reciprocal two-loop plane topology',not topology['unresolved'] and graph['counts']==COUNTS
                and graph['surface_record_types']=={'plane-surface':1})
            check(filename+' distinct nonserialized naming scope',view['view_tag_summary']['origin_map']==view['origin_map']
                and 'nonserialized' in view['view_tag_summary']['scope'] and not view['view_tag_summary']['unresolved'])
            consistency=view['derived_stored_geometry_consistency']
            check(filename+' derived circle/plane/endpoints consistent after identity',consistency['same_center']
                and consistency['positive_distinct_radii'] and consistency['coplanar_with_qualified_plane']
                and consistency['typed_domain_endpoints_consistent'])
            for edge_id in graph['edge_indices']:
                edge=nodes[edge_id];curve=nodes[edge['curve_index']];point=nodes[nodes[edge['start_vertex_index']]['point_index']]
                difference=[a-b for a,b in zip(point['raw_origin'],curve['raw_origin'])]
                check(filename+' typed circular endpoint locus'+str(edge_id),abs(sum(v*v for v in difference)-curve['raw_major_radius']**2)<1e-12
                    and abs(sum(a*b for a,b in zip(difference,curve['normal'])))<1e-12)
            named=[]
            if filename.endswith('/untrim_manual.f3d'):
                descriptor=primary[289];recipe=decode_counted_recipe(data,primary[reference(data[descriptor.body:descriptor.end],4)])
                correspondence=match_recipe_tag_names(recipe,view['view_tag_summary'],parsed=view['view_parsed'])
                check('Manual exact complete edge and face names in literal view',[e['candidate_count'] for e in correspondence['name_entries']]==[1,1])
                candidates=[e['candidates'][0] for e in correspondence['name_entries']]
                check('Manual named typed operands in qualified BODY',[c['owner_kind'] for c in candidates]==['edge','face']
                    and all(c['body_graph_membership']==[graph['body_index']] for c in candidates))
                edge=nodes[candidates[0]['owner_record_index']];coedge=nodes[edge['first_coedge_index']];loop=nodes[coedge['loop_index']]
                check('Manual named edge and loop reciprocal to named face',loop['face_index']==candidates[1]['owner_record_index']
                    and coedge['edge_index']==edge['index'] and coedge['next_coedge_index']==coedge['previous_coedge_index']==coedge['index'])
                named=dict(correspondence=correspondence,selected_edge_origin=origins[edge['index']],
                    selected_face_origin=origins[loop['face_index']],selected_loop_origin=origins[loop['index']],
                    selected_coedge_origin=origins[coedge['index']])
                check('Manual actual stored identifier4 retained independently',binding['stored_handle']==4
                    and nodes[graph['body_index']]['stored_entity_id']==4)
                view_fixture=(blob,parsed,history,binding,view)
            base.update(expected_provenance={k:v for k,v in view.items() if k not in ('view_parsed','topology')},
                expected_topology=topology,expected_view_record_token_sha256=[dict(
                    view_record_index=r['index'],token_sha256=digest(r['tokens'])) for r in view['view_parsed']['records']],
                named_manual_boundary_proof=named)
        check(filename+' canonical inputs/tags/topology unchanged',parsed==before
            and initial_tags==decode_asm_generic_tags(blob,parsed,allow_fpm_tracking=True) and initial_topology==decode_topology(parsed))
        truth_path=(ROOT/filename).parent/'ground_truth.json';truth=json.loads(truth_path.read_text());actual=next(s for s in truth['samples'] if s['file']==Path(filename).name)
        base['saved_API_context']=dict(source=str(truth_path.relative_to(ROOT)),source_sha256=sha(truth_path),settings=actual['settings'],
            scope='Actual modeling controls only; no source-edge/API handle identity, historical-state evaluator or inner/outer native flag is inferred')
        samples.append(base)
    historical=json.loads((ROOT/'asm-name-version-decoding.json').read_text())
    archives={}
    for sample in historical['samples']:
        filename=sample['archive']
        if filename not in archives:archives[filename]=read_members(ROOT/filename,zstd)
        current=decode_asm_name_versions(archives[filename][sample['member']])
        check(filename+' '+sample['member']+' frozen default name-version dictionary exact',current==sample['expected_summary'])
        old_defaults.append(dict(archive=filename,member=sample['member'],full_default_dictionary_exact=True))
    # Keep the previous three-state box materializer independent and unchanged.
    from materialize_asm_alternative import materialize_asm_alternative
    boxfile='edgemodes-52695761f185/fillet_curvature.f3d';boxmembers=read_members(ROOT/boxfile,zstd)
    boxname=next(n for n in boxmembers if n.endswith('.smbh'));boxblob=boxmembers[boxname]
    box=materialize_asm_alternative(boxblob)
    check('Old three-state box materializer retains captured topology',box['state_slot']==0 and box['pointer_side']==0
        and box['qualified_dangling_pointer_count']==0 and not box['topology']['unresolved'])
    try:materialize_untrim_cache(boxblob,initial_body_record_index=1,stored_body_identifier=1)
    except ValueError as error:box_rejection=str(error)
    else:raise AssertionError('Old box admitted by Untrim-only materializer')
    blob,parsed,history,binding,view=view_fixture
    def guard(label,mutate=None,**kwargs):
        raw=bytearray(blob)
        if mutate is not None:mutate(raw)
        args=dict(initial_body_record_index=binding['asm_body_index'],stored_body_identifier=binding['stored_handle']);args.update(kwargs)
        try:materialize_untrim_cache(bytes(raw),**args)
        except (ValueError,KeyError,IndexError,TypeError,struct.error) as error:reason=str(error)
        else:raise AssertionError(label)
        guards.append(dict(guard=label,rejected=True,reason=reason))
    guard('Reject supplied stored identifier differing from raw initial BODY',stored_body_identifier=99)
    guard('Reject auxiliary initial BODY as native mapped source',initial_body_record_index=1)
    target=view['source_body_pair']['pointer_sides'][0]['inspection_record_index']
    guard('Reject changed paired BODY identifier',lambda raw:struct.pack_into('<q',raw,parsed['records'][target]['tokens'][1]['offset']+1,5))
    pair=view['source_body_pair']['pointer_sides'][0]
    face_origin=next(o for o in view['origin_map'] if o['kind']=='face' and o['section']=='trailing_states')
    guard('Reject journal BODY alias with FACE kind',lambda raw:struct.pack_into('<q',raw,pair['token_offset']+1,face_origin['geometry_entity_ordinal']))
    edge_origin=next(o for o in view['origin_map'] if o['kind']=='edge' and o['geometry_entity_ordinal']==65)
    edge_record=parsed['records'][edge_origin['inspection_record_index']]
    guard('Reject dangling pointer to removed nested metadata',lambda raw:struct.pack_into('<q',raw,edge_record['tokens'][8]['offset']+1,26))
    curve_ordinal=edge_record['tokens'][8]['value']
    curve_record=parsed['records'][history['geometry_entities'][curve_ordinal]['inspection_record_index']]
    guard('Reject corrupted named circular center after typed identity qualification',
        lambda raw:struct.pack_into('<d',raw,curve_record['tokens'][3]['offset']+1,.125))
    coedge_origin=next(o for o in view['origin_map'] if o['kind']=='coedge' and o['geometry_entity_ordinal']==68)
    coedge_record=parsed['records'][coedge_origin['inspection_record_index']]
    guard('Reject nonreciprocal singleton boundary coedge',lambda raw:struct.pack_into('<q',raw,coedge_record['tokens'][4]['offset']+1,61))
    def duplicate(raw):
        state=parsed['records'][history['journal_states'][0]['inspection_record_index']];at=12+3*view['source_body_pair']['entry_ordinal']
        begin,end=state['tokens'][at]['offset'],state['tokens'][at+3]['offset'];insert=state['tokens'][-3]['offset'];raw[insert:insert]=blob[begin:end]
    guard('Reject duplicated complete BODY journal pair',duplicate)
    stale=copy.deepcopy(parsed);stale['records'][target]['tokens'][1]['value']=5
    guard('Reject stale supplied source parse',parsed=stale)
    modified_blob,modified_parsed,version=modified_fixture
    def nested_guard(label,token,value):
        raw=bytearray(modified_blob);struct.pack_into('<q',raw,token['offset']+1,value)
        answer=decode_asm_name_versions(bytes(raw),allow_modified_nested=True)
        if answer['decoded']:raise AssertionError(label)
        guards.append(dict(guard=label,rejected=True,reason='; '.join(r['reason'] for r in answer['unresolved'])))
    child=modified_parsed['records'][version['initial_attribute']['validated_nested_metadata']['record_index']]
    nested_guard('Reject modified nested family without child-parent backlink',child['tokens'][4],version['owner_face_geometry_entity_ordinal'])
    trailing=modified_parsed['records'][version['trailing_attribute']['record_index']]
    nested_guard('Reject modified nested family with unrelated complete tuple',trailing['tokens'][-2],999)
    return dict(scope=SCOPE,samples=samples,old_name_version_default_controls=old_defaults,
        validation=dict(saved_Untrim_archives=4,qualified_literal_views=2,manual_selected_loop_proofs=1,
            modified_nested_opt_in_cases=2,frozen_default_summaries_exact=len(old_defaults),
            focused_checks=len(checks),malformed_guards=len(guards),main_calls=0,live_API_calls=0),
        checks=checks,malformed_guards=guards,
        old_three_state_box_control=dict(archive=boxfile,member=boxname,expected_old_materializer_summary=box,
            new_materializer_rejection=box_rejection),
        integration=dict(callable='materialize_untrim_cache(blob, *, initial_body_record_index, stored_body_identifier, parsed=None, history=None)',
            expected_provenance='samples[].expected_provenance is every public view field except view_parsed/topology; Manual native source may embed it exactly',
            origins='Per-record inspection indices/geometry ordinals/byte bounds remain separate from dense view indices; wrapped view_tag_summary carries the same origin_map',
            naming_opt_in='decode_asm_name_versions(..., allow_modified_nested=True) admits only the captured modified two/one tuple family with the already validated nested metadata child'),
        source_sha256={f:sha(ROOT/f) for f in ('materialize_untrim_cache.py','validate_untrim_cache.py','decode_asm_name_versions.py',
            'decode_asm_history.py','decode_asm_recipe_tags.py','decode_brep.py','materialize_asm_alternative.py')},
        historical_name_version_report_sha256=sha(ROOT/'asm-name-version-decoding.json'),
        limitations=['The literal view selects a journal pair table, not chronological replay or geometry before Untrim',
            'Matching BODY stored identifiers qualify consistency of the explicit pair, not a historical native identity bridge',
            'Only the observed five-state two-circular-loop planar topology is admitted; six-state External/All views remain rejected',
            'Manual source naming is unique in this qualified nonserialized view; no current/persistent/API identity or original serialized pointer claim follows',
            'Internal is an independent same-framing holdout; the new native Manual branch remains a separate caller decision',
            'Canonical initial tags/topology and all prior default name-version dictionaries remain unchanged; no other reader is edited'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--zstd-library');p.add_argument('--output',default='untrim-cache-decoding.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(z);Path(a.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['validation'],sort_keys=True))


if __name__=='__main__':main()
