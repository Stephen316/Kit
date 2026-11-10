"""Focused native PathPattern key/source cache joins, with no main-reader calls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_body_bindings import decode_body_bindings
from decode_path_pattern_cache_evidence import decode_path_pattern_cache_evidence, SCOPE
import decode_path_pattern_cache_evidence as reader
from decode_placement import decode_placement
from decode_sketch import decode_sketches, reference
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
BODY_FILES=tuple('pathpatterns-de9857f6a1bc/'+n+'.f3d' for n in
    ('spacing','extent','start_offset','flipped','symmetric','arc_identical','arc_along','multiple_bodies','suppressed_instance'))+tuple(
    'pathpatterncomposites-b6b4cf615504/'+n+'.f3d' for n in
    ('composite_identical','composite_along','spline_along','composite_multiple'))
FEATURE_CONTROLS=tuple('pathpatterninputs-7edfa558db34/'+n+'.f3d' for n in ('feature_optimized','feature_identical'))
CONTROLS=('rectmodes-a069f8f4b8a2/body_one.f3d','rectmodes-a069f8f4b8a2/feature_optimized.f3d',
    'circularmodes-45f859c1f1b6/body_full.f3d')
FILES=BODY_FILES+FEATURE_CONTROLS+CONTROLS


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepared(archive,zstd):
    data,records,features,member,members=load(ROOT,archive,zstd)
    decode_sketches(data,records,features)
    decode_placement(data,records,features)
    raw=decode_body_bindings(data,records,member,dict(streams=[dict(member=n,
        complete_token_stream=True,declared_root_records=[]) for n in members if n.endswith('.smbh')]))
    return data,records,features,member,members,raw


def validate(zstd):
    samples,checks,guards=[],[],[]
    counts=dict(element_cache_groups=0,result_BODY_correspondences=0,typed_vertex_pairs=0,
        source_BODY_routes=0,literal_suppressed_groups=0)
    maximum=0.
    saved=None
    suppressed_case=None

    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)

    def inactive(*_args):
        raise AssertionError('BODY/default control invoked Feature callback')

    for archive in FILES:
        loaded=prepared(archive,zstd)
        data,records,features,member,members,raw=loaded
        original=copy.deepcopy((features,raw))
        out=decode_path_pattern_cache_evidence(*loaded)
        check(archive+' input metadata and bindings unchanged',(features,raw)==original)
        sample=dict(archive=archive,archive_sha256=sha(ROOT/archive),member=member,expected_summary=out)
        if archive not in BODY_FILES:
            check(archive+' complete default empty dictionary',out==dict(decoded=[],unresolved=[],scope=SCOPE))
            sample['role']='defaultFeatureSkip' if archive in FEATURE_CONTROLS else 'unrelatedControl'
            samples.append(sample)
            continue
        sample['role']='BODYpositive'
        check(archive+' callback remains inactive on BODY',decode_path_pattern_cache_evidence(*loaded,feature_source_resolver=inactive)==out)
        check(archive+' exactly one qualified BODY row',len(out['decoded'])==1 and not out['unresolved'])
        row=out['decoded'][0]
        check(archive+' BODY identity and unknown API/current semantics',row['pattern_entity_type']=='Bodies'
            and row['stored_entity_type_code']==2 and all(row[k] is None for k in ('API_element_identity','logical_grid_identity','current_placement')))
        primary={r.object_id:r for r in records if r.is_primary}
        control=primary[row['control_record_object_id']]
        cb=data[control.body:control.end]
        pair_count=struct.unpack_from('<I',cb,138)[0]
        pairs=[list(struct.unpack_from('<QQ',cb,142+16*i)) for i in range(pair_count)]
        quantity=pair_count+1
        cursor=142+16*pair_count+4+11*quantity+33
        mask_count=struct.unpack_from('<I',cb,cursor)[0]
        mask=list(struct.unpack_from('<'+'I'*mask_count,cb,cursor+4))
        active=[p for p in pairs if p[0] not in mask]
        check(archive+' independent raw pair/mask framing',len(cb)==cursor+4+4*mask_count
            and pairs==row['stored_instance_ordinal_pairs'] and mask==row['stored_suppressed_element_ordinals']
            and active==row['active_instance_ordinal_pairs'] and 0 not in mask)
        element_proof=[]
        for identity,ordinal in zip(row['element_record_object_ids'],row['element_record_ordinals']):
            rec=primary[identity];payload=data[rec.body:rec.end]
            check(archive+' typed explicit element '+str(identity),rec.class_guid==reader.ELEMENT
                and len(payload)==17 and payload[:2]==bytes(2)
                and struct.unpack_from('<I',payload,2)[0]==ordinal and reference(payload,6)==control.object_id)
            element_proof.append(dict(object_id=identity,class_guid=rec.class_guid,record_offset=rec.start,
                stored_ordinal=ordinal,controller_object_id=reference(payload,6),payload_hex=payload.hex()))
        check(archive+' independent element/pair/mask coverage',row['element_record_ordinals']==list(range(quantity))
            and {g['stored_element_ordinal'] for g in row['element_cache_groups']}=={p[0] for p in active}
            and {g['stored_element_ordinal'] for g in row['suppressed_cache_groups']}==set(mask)
            and row['complete_controller_source_group_bijection'])
        source_ids=set(row['source_native_body_object_ids'])
        source_by_id={s['source_native_body_object_id']:s for s in row['source_cache_bodies']}
        expected={(key,s['stored_source_naming_prefix'][0]) for _,key in active for s in source_by_id.values()}
        actual=set();result_ids=set();anchor_ids=set()
        for group in row['element_cache_groups']:
            counts['element_cache_groups']+=1
            check(archive+' literal controller group '+str(group['stored_element_ordinal']),
                dict(pairs)[group['stored_element_ordinal']]==group['stored_naming_key']
                and {b['source_native_body_object_id'] for b in group['cache_bodies']}==source_ids)
            for b in group['cache_bodies']:
                counts['result_BODY_correspondences']+=1
                source=source_by_id[b['source_native_body_object_id']]
                prefix=source['stored_source_naming_prefix']
                fit=b['measured_relative_rigid_fit'];binding=b['result_body_binding'];anchor=b['result_body_anchor']
                maximum=max(maximum,fit['maximum_vertex_residual_raw'])
                counts['typed_vertex_pairs']+=fit['matched_vertex_count']
                actual.add((group['stored_naming_key'],prefix[0]))
                anchor_ids.add(b['result_anchor_object_id']);result_ids.add(b['result_native_body_object_id'])
                check(archive+' exact complete inherited name/source/key tuple '+str(b['result_native_body_object_id']),
                    b['stored_face_naming_components']==prefix+[row['uninterpreted_common_feature_naming_component'],group['stored_naming_key']]
                    and anchor['native_body_object_id']==binding['native_body_object_id']==b['result_native_body_object_id']
                    and anchor['source_owner_object_id']==row['feature_object_id']
                    and binding['stored_handle']==binding['asm_stored_entity_id'])
                check(archive+' full eight fixed vertex identities '+str(b['result_native_body_object_id']),
                    fit['matched_vertex_count']==8 and fit['maximum_vertex_residual_raw']<1e-8
                    and len({tuple(tuple(x) for x in p['incident_face_name_keys']) for p in fit['vertex_correspondence']})==8)
        check(archive+' exact active pair/source product and owned result set',actual==expected
            and len(actual)==len(result_ids)==len(anchor_ids)==len(active)*len(source_ids)
            and anchor_ids==set(row['owned_result_anchor_object_ids']) and not source_ids&result_ids)
        counts['source_BODY_routes']+=len(source_ids)
        counts['literal_suppressed_groups']+=len(mask)
        feature=primary[row['feature_object_id']];fb=data[feature.body:feature.end]
        check(archive+' exact native counted anchor list',struct.unpack_from('<I',fb,32)[0]==len(anchor_ids)
            and [reference(fb,36+11*i) for i in range(len(anchor_ids))]==row['owned_result_anchor_object_ids'])
        truth_path=(ROOT/archive).parent/'ground_truth.json'
        truth=json.loads(truth_path.read_text())
        api=next(s for s in truth['samples'] if s['file']==Path(archive).name)['settings']
        check(archive+' actual saved input/result counts and literal suppression corroborate',
            api.get('input_body_count',api.get('input_count'))==len(source_ids)
            and api['result_body_count']==len(source_ids)+len(result_ids) and api['suppressed_element_ids']==mask)
        sample.update(native_controller_proof=dict(object_id=control.object_id,record_offset=control.start,
            payload_hex=cb.hex(),pairs=pairs,literal_suppressed_ordinals=mask,active_pairs=active,elements=element_proof),
            saved_API_settings=api,truth_source=str(truth_path.relative_to(ROOT)),truth_sha256=sha(truth_path),
            API_correspondence_scope='Saved counts/controls corroborate only; no API element handle, matrix or per-BODY assignment is inferred')
        if archive.endswith('/multiple_bodies.f3d'):saved=loaded,row
        if mask:
            check('Captured literal suppressed1 excludes naming305 only',mask==[1] and pairs==[[1,305],[2,306],[3,307]]
                and active==[[2,306],[3,307]] and {g['stored_naming_key'] for g in row['element_cache_groups']}=={306,307})
            suppressed_case=loaded,row
        samples.append(sample)

    loaded,row=saved
    data,records,features,member,members,raw=loaded
    primary={r.object_id:r for r in records if r.is_primary}

    def rejected(label,changed_data=None,changed_members=None,before_fit=True,case=loaded):
        d,rs,fs,m,ms,bindings=case
        old_fit=reader._fit
        def forbidden(*_args):raise AssertionError('Malformed identity reached fit')
        if before_fit:reader._fit=forbidden
        try:
            out=decode_path_pattern_cache_evidence(changed_data if changed_data is not None else d,
                rs,fs,m,changed_members if changed_members is not None else ms,bindings)
        finally:reader._fit=old_fit
        check(label,not out['decoded'] and len(out['unresolved'])==1)
        guards.append(dict(guard=label,rejected=True,reason=out['unresolved'][0]['reason'],verified_no_fit_before_rejection=before_fit))

    control=primary[row['control_record_object_id']]
    changed=bytearray(data)
    struct.pack_into('<Q',changed,control.body+142+16+8,row['stored_instance_ordinal_pairs'][0][1])
    rejected('Duplicate opaque naming key',changed_data=bytes(changed))
    element=primary[row['element_record_object_ids'][0]]
    changed=bytearray(data);struct.pack_into('<Q',changed,element.body+7,row['feature_object_id'])
    rejected('Typed element controller backlink changed',changed_data=bytes(changed))
    anchor=primary[row['owned_result_anchor_object_ids'][0]]
    changed=bytearray(data);struct.pack_into('<Q',changed,anchor.body+92,row['control_record_object_id'])
    rejected('Owned result anchor receiver changed',changed_data=bytes(changed))
    mapping=primary[row['mapping_record_object_id']]
    changed=bytearray(data);struct.pack_into('<Q',changed,mapping.body+6,999999)
    rejected('Explicit stored BODY identifier join corrupted',changed_data=bytes(changed))
    blob_member=row['history_blob_member'];blob=members[blob_member];parsed=inspect_asm(blob)
    first=row['element_cache_groups'][0]['cache_bodies'][0]
    aid=first['complete_result_face_naming_proof'][0]['owner_attribute_indices'][0]
    changed=bytearray(blob);struct.pack_into('<q',changed,parsed['records'][aid]['tokens'][4]['offset']+1,1)
    rejected('Complete generic FACE owner chain changed',changed_members={**members,blob_member:bytes(changed)})
    point_id=first['measured_relative_rigid_fit']['vertex_correspondence'][-1]['target']['point_index']
    point=parsed['records'][point_id]
    changed=bytearray(blob);struct.pack_into('<d',changed,point['tokens'][3]['offset']+1,point['tokens'][3]['value'][0]+.125)
    rejected('Identity-fixed eighth vertex contradicts fit',changed_members={**members,blob_member:bytes(changed)},before_fit=False)
    sl,srow=suppressed_case;sd,srs,sfs,sm,sms,sraw=sl
    sc=next(r for r in srs if r.is_primary and r.object_id==srow['control_record_object_id'])
    # The final uint32 is the explicitly counted one-item mask, not a byte search.
    changed=bytearray(sd);struct.pack_into('<I',changed,sc.end-4,2)
    rejected('Wrong filtered native mask contradicts owned naming product',changed_data=bytes(changed),case=sl)
    changed=bytearray(sd);struct.pack_into('<I',changed,sc.end-4,0)
    rejected('Unobserved seed0 suppression is explicit rejection',changed_data=bytes(changed),case=sl)
    return dict(scope=SCOPE,samples=samples,validation=dict(positive_BODY_archives=len(BODY_FILES),
        default_Feature_skip_controls=len(FEATURE_CONTROLS),complete_unrelated_controls=len(CONTROLS),
        **counts,maximum_fit_residual_raw=maximum,focused_checks=len(checks),malformed_guards=len(guards),
        no_fit_identity_guards=sum(g['verified_no_fit_before_rejection'] for g in guards),main_calls=0,live_API_calls=0),
        checks=checks,malformed_guards=guards,
        integration=dict(callable='decode_path_pattern_cache_evidence(data,records,features,member,members,body_blob_bindings,*,feature_source_resolver=None)',
            stream='path_pattern_cache_evidence',owner_attachment='feature.path_pattern_cache_evidence',owner_key='feature_object_id',
            goldens='samples[].expected_summary FULL; BODY/defaultFeatureSkip/unrelatedControl roles explicit',
            existing_outputs='Evidence only; no tool settings, old warnings, placement matrices or native records changed'),
        source_sha256={n:sha(ROOT/n) for n in ('decode_path_pattern_cache_evidence.py','validate_path_pattern_cache_evidence.py',
            'decode_path_patterns.py','decode_path_pattern_composites.py','decode_circular_placement_evidence.py',
            'decode_body_asm_identifiers.py','decode_body_selections.py','decode_asm_recipe_tags.py','decode_brep.py')},
        limitations=['Only complete six-uniquely-named-face/eight-vertex/twelve-edge identity-transform BODY graphs are admitted by the reused strict naming/incidence validators',
            'Opaque naming keys join complete typed names before fitting; result-list order and coordinates never select a BODY',
            'Literal nonseed mask filters native pair membership only; no API ID, final visibility or regenerated suppression semantics',
            'Measured relative matrices describe initial stored cache geometry with identity BODY transforms; no analytic path traversal or serialized transform claimed',
            'Native and saved API control/result counts corroborate independently; there is no API element-to-BODY assignment or future native writer',
            'Default Feature inputs are skipped. The separate opt-in source callback must prove its own complete typed Feature route; BODY callbacks remain inactive'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library')
    parser.add_argument('--output',default='path-pattern-cache-evidence-decoding.json')
    args=parser.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd)
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['validation'],sort_keys=True))
