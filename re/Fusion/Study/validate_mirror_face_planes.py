"""Eight saved Mirror support/control cases, exact native names before geometry."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_body_bindings import decode_body_bindings
from decode_mirror_face_planes import decode_mirror_face_planes, SCOPE
from decode_mirror_modes import MIRROR, decode_mirror_modes
from decode_placement import decode_placement
from decode_selection import known_construction_entities
from decode_sketch import decode_sketches
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
POSITIVE='mirrorfeatures-1ffa1b15c612/body_brep_face_plane.f3d'
CONTROLS=tuple('mirrorfeatures-1ffa1b15c612/'+n+'.f3d' for n in ('feature_optimized','feature_identical','feature_adjust'))+(
    'tools-fda3948848f4/Mirror.f3d','surfacebounds-ac801bb00fae/untrim_all.f3d',
    'surfacetools-856ca50cf4c7/offset_positive.f3d','pathpatterns-de9857f6a1bc/spacing.f3d')
FILES=(POSITIVE,)+CONTROLS


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepared(archive,zstd):
    data,records,features,member,members=load(ROOT,archive,zstd)
    decode_sketches(data,records,features)
    decode_placement(data,records,features)
    raw=decode_body_bindings(data,records,member,dict(streams=[dict(member=n,
        complete_token_stream=True,declared_root_records=[]) for n in members if n.endswith('.smbh')]))
    return data,records,features,member,members,raw


def validate(zstd):
    samples,checks,guards=[],[],[]
    old_report=json.loads((ROOT/'mirror-mode-decoding.json').read_text())
    legacy={s['archive']:s['decoded'] for s in old_report['samples']}

    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)

    def legacy_settings(loaded):
        d,rs,fs,_,_,_=loaded
        f=next(f for f in fs if f['class_guid']==MIRROR)
        rec=next(r for r in rs if r.is_primary and r.object_id==f['object_id'])
        return decode_mirror_modes(d,rs,d[rec.body:rec.end],f,known_construction_entities(d,rs,fs),fs)

    saved=None
    for archive in FILES:
        loaded=prepared(archive,zstd)
        data,records,features,member,members,raw=loaded
        original=copy.deepcopy((features,raw))
        before=legacy_settings(loaded) if archive in legacy else None
        out=decode_mirror_face_planes(*loaded)
        check(archive+' caller feature and mapping dictionaries unchanged',(features,raw)==original)
        sample=dict(archive=archive,archive_sha256=sha(ROOT/archive),member=member,expected_summary=out)
        if before is not None:
            check(archive+' legacy complete Mirror settings match historical golden',before==legacy[archive])
            check(archive+' legacy complete Mirror settings unchanged after new helper',legacy_settings(loaded)==before)
            sample['expected_legacy_settings']=before
        if archive!=POSITIVE:
            check(archive+' complete no-candidate control',out==dict(decoded=[],unresolved=[],scope=SCOPE))
            sample['empty_control']=True
            samples.append(sample)
            continue
        check('One complete cached face plane',len(out['decoded'])==1 and not out['unresolved'])
        row=out['decoded'][0]
        source=row['native_plane_source']['face'];context=row['native_plane_source']['typed_context']
        binding=row['source_body_binding'];operand=row['cached_operand'];plane=row['cache_plane']
        check('Explicit receiving Mirror/proxy/descriptor/recipe identity',row['feature_object_id']==377
            and row['plane_selection_record_object_id']==395 and row['descriptor_object_id']==398
            and row['recipe']['object_id']==401 and row['exact_recipe_payload_replay'])
        check('Fresh anchored BODY and stored ID are distinct namespaces',source['body_anchor_object_id']==358
            and source['native_body_object_id']==binding['native_body_object_id']==354
            and source['source_owner_object_id']==322 and binding['stored_handle']==binding['asm_stored_entity_id']==8
            and binding['asm_body_index']==operand['body_record_index']==2)
        check('Complete FACE name matched inside previously mapped BODY',row['recipe']['name_table'][0]['terms'][0]['name']=='2'
            and row['recipe']['name_table'][0]['terms'][0]['stored_reference_components_int32']==[304]
            and len(row['mapped_body_FACE_candidates'])==1
            and row['mapped_body_FACE_candidates'][0]['owner_kind']=='face'
            and row['mapped_body_FACE_candidates'][0]['body_graph_membership']==[2]
            and row['mapped_body_FACE_candidates'][0]['owner_record_index']==operand['face_record_index']==97)
        check('Owned context retains matching namespace and absent route',context['context_object_id']==408
            and context['optional_context_recipe_route'] is None
            and context['namespace_text']==source['namespace_text'] and context['entity_guid_text']==source['entity_guid_text'])
        support=row['support_provenance']
        check('Literal support sources and anchor owner independently recorded',support['support_object_id']==399
            and support['support_source_record_object_ids']==[322]
            and support['historical_anchor_source_owner_object_id']==322
            and support['historical_body_anchor_object_id']==358
            and len(support['stored_support_cache_bytes_hex'])==2
            and all(len(v)==16 for v in support['stored_support_cache_bytes_hex']))
        check('Typed plane and four reciprocal boundary copies retained',operand['surface']['kind']=='plane-surface'
            and operand['surface']['index']==165 and len(operand['incidence_routes'])==4
            and len(operand['boundary_edges'])==4
            and all(e['curve']['kind']=='straight-curve' for e in operand['boundary_edges']))
        check('After-identity geometry is finite/coplanar and equation derived',plane['raw_origin']==[-3.,-3.,3.]
            and plane['raw_normal']==plane['normalized_unit_normal']==[0.,0.,1.]
            and plane['normalized_plane_equation']==[0.,0.,1.,-3.]
            and plane['derived_maximum_boundary_plane_residual_raw']==0.)
        truth_path=(ROOT/POSITIVE).parent/'ground_truth.json'
        truth=json.loads(truth_path.read_text());api=next(s for s in truth['samples'] if s['file']==Path(POSITIVE).name)
        actual=api['actual_mirror_plane']
        check('Saved actual plane getter corroborates after exact native identity',actual['entity_type']=='adsk::fusion::BRepFace'
            and actual['origin_cm']==plane['raw_origin'] and actual['normal']==plane['normalized_unit_normal'])
        check('Legacy native plane geometry remains explicitly None',before['plane'] is None
            and before['plane_source']['plane_geometry'] is None)
        check('API/current/persistent/state/reflection claims remain absent',all(row[k] is None for k in
            ('API_handle_identity','persistent_source_identity','current_source_identity','qualified_historical_state','reflection_geometry')))
        for native in row['native_record_proof']:
            recs=[r for r in records if r.is_primary and r.object_id==native['object_id']]
            check('Exact raw native proof replay '+str(native['object_id']),len(recs)==1
                and data[recs[0].body:recs[0].end].hex()==native['payload_hex'])
        sample.update(saved_API_correspondence=dict(truth_source=str(truth_path.relative_to(ROOT)),truth_sha256=sha(truth_path),
            actual_type=actual['entity_type'],actual_origin_cm=actual['origin_cm'],actual_normal=actual['normal'],
            actual_surface_type=actual['surface_type'],actual_health_state=api['settings']['health_state'],
            scope='Independent geometry corroboration after native name/BODY association; opaque API tokens do not assign cache identity'),
            support_role_counterexample=json.loads((ROOT/'selection-context-variant-decoding.json').read_text())['counterexample'])
        saved=loaded,row
        samples.append(sample)

    loaded,row=saved
    data,records,features,member,members,raw=loaded
    primary={r.object_id:r for r in records if r.is_primary}
    descriptor=primary[row['descriptor_object_id']]

    def rejected(label,changed_data=None,changed_records=None,changed_members=None):
        out=decode_mirror_face_planes(changed_data if changed_data is not None else data,
            changed_records if changed_records is not None else records,features,member,
            changed_members if changed_members is not None else members,raw)
        check(label,not out['decoded'] and len(out['unresolved'])==1)
        guards.append(dict(guard=label,rejected=True,reason=out['unresolved'][0]['reason']))

    def native_change(identity,offset,value):
        changed=bytearray(data);rec=primary[identity]
        changed[rec.body+offset:rec.body+offset+len(value)]=value
        # Native byte-scope proof requires this changed Design member too.
        return bytes(changed),{**members,member:bytes(changed)}

    changed,ms=native_change(descriptor.object_id,266,struct.pack('<Q',322))
    rejected('Owned descriptor receiving Mirror changed',changed_data=changed,changed_members=ms)
    changed,ms=native_change(row['support_provenance']['support_object_id'],32,struct.pack('<Q',388))
    rejected('Native support reciprocal descriptor changed',changed_data=changed,changed_members=ms)
    changed,ms=native_change(row['support_provenance']['historical_body_anchor_object_id'],81,struct.pack('<Q',275))
    rejected('Historical anchor redirected to different mapped BODY',changed_data=changed,changed_members=ms)
    rejected('Duplicate primary descriptor identity',changed_records=records+[descriptor])
    recipe_record=primary[row['recipe']['object_id']]
    changed,ms=native_change(recipe_record.object_id,row['recipe']['payload_relative_offset'],struct.pack('<i',1))
    rejected('Unobserved direct face operation payload',changed_data=changed,changed_members=ms)
    term_offset=data[recipe_record.body:recipe_record.end].index(bytes.fromhex('30010000'))
    changed,ms=native_change(recipe_record.object_id,term_offset,struct.pack('<i',301))
    rejected('Complete name points outside prequalified BODY FACE namespace',changed_data=changed,changed_members=ms)
    blob_member=row['history_blob_member'];blob=members[blob_member];parsed=inspect_asm(blob)
    surface=parsed['records'][row['cached_operand']['surface']['index']]
    changed=bytearray(blob)
    struct.pack_into('<3d',changed,surface['tokens'][4]['offset']+1,0.,0.,0.)
    rejected('Typed plane stored normal is degenerate',changed_members={**members,blob_member:bytes(changed)})
    changed=bytearray(blob)
    struct.pack_into('<d',changed,surface['tokens'][3]['offset']+1+16,plane['raw_origin'][2]+.125)
    rejected('Identity-fixed boundary contradicts stored plane origin',changed_members={**members,blob_member:bytes(changed)})
    changed=bytearray(blob)
    struct.pack_into('<3d',changed,surface['tokens'][4]['offset']+1,1.7e308,1.7e308,1.7e308)
    rejected('Finite components whose vector norm overflows cannot publish a normalized plane',
        changed_members={**members,blob_member:bytes(changed)})
    return dict(scope=SCOPE,samples=samples,validation=dict(positive_archives=1,complete_empty_controls=7,
        legacy_Mirror_full_dictionaries_exact=4,explicit_BODY_stored_ID_joins=1,complete_FACE_names=1,
        typed_boundary_edges=4,saved_API_origin_normal_comparisons=2,focused_checks=len(checks),
        malformed_guards=len(guards),main_calls=0,live_API_calls=0),checks=checks,malformed_guards=guards,
        source_sha256={n:sha(ROOT/n) for n in ('decode_mirror_face_planes.py','validate_mirror_face_planes.py',
            'decode_mirror_modes.py','decode_owned_surface_selection.py','decode_recipe_components.py',
            'decode_asm_recipe_tags.py','decode_body_asm_identifiers.py','decode_untrim_sources.py')},
        integration=dict(callable='decode_mirror_face_planes(data,records,features,member,members,body_blob_bindings)',
            summary='samples[].expected_summary FULL including seven empty controls',stream='mirror_face_planes',
            feature_attachment='feature.mirror_face_plane_cache',row_key='feature_object_id',
            legacy_geometry='plane and plane_source.plane_geometry remain None'),
        limitations=['Complete term-group and FACE uniqueness is scoped to the explicitly mapped BODY before geometry; no coordinate proximity or lexical/numeric design-ID identity',
            'Literal native support sources and anchor source owner remain separate roles, including the preserved older mismatch counterexample',
            'Only captured singleton BODY/noncombine Mirror face_recipe_data [0,-1] with absent context route and planar four-Line boundary is qualified',
            'Plane equation is derived from a raw initial cache with identity BODY transform; no current or before-feature state, world placement, API handle, reflection, native UV orientation or regeneration claimed'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library')
    parser.add_argument('--output',default='mirror-face-plane-decoding.json')
    args=parser.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd)
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['validation'],sort_keys=True))
