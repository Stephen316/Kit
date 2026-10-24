"""Native Mirror source/anchor/component qualification without reflection fits."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from decode_body_bindings import decode_body_bindings
from decode_mirror_cache_sources import qualify_mirror_cache_sources, SCOPE, MIRROR
from decode_mirror_modes import decode_mirror_modes
from decode_placement import decode_placement
from decode_selection import known_construction_entities
from decode_sketch import decode_sketches, reference
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
POSITIVES=tuple('mirrorfeatures-1ffa1b15c612/'+n+'.f3d' for n in
    ('body_brep_face_plane','feature_optimized','feature_identical','feature_adjust'))+(
    'tools-fda3948848f4/Mirror.f3d','bodyselections-62e42366c722/mirror_two_bodies_plane.f3d',
    'remainingbodyinputs-7b3357274e85/mirror_two_features.f3d')
CONTROLS=('remainingbodyinputs-7b3357274e85/mirror_boss_faces.f3d',
    'datummirrorsupport-3a854f334428/offset_selected_support.f3d',
    'surfacetools-856ca50cf4c7/offset_positive.f3d','surfacebounds-ac801bb00fae/untrim_all.f3d',
    'pathpatterns-de9857f6a1bc/spacing.f3d')
FILES=POSITIVES+CONTROLS


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepared(archive,zstd):
    data,records,features,member,members=load(ROOT,archive,zstd)
    decode_sketches(data,records,features)
    decode_placement(data,records,features)
    bindings=decode_body_bindings(data,records,member,dict(streams=[dict(member=n,
        complete_token_stream=True,declared_root_records=[]) for n in members if n.endswith('.smbh')]))
    return data,records,features,member,members,bindings


def validate(zstd):
    checks,samples,guards=[],[],[]
    legacy={s['archive']:s['decoded'] for s in json.loads((ROOT/'mirror-mode-decoding.json').read_text())['samples']}
    saved={};counts=dict(source_BODY_routes=0,owned_result_anchors=0,origin_plane_owners=0,
        stored_Offset_plane_owners=0,named_face_plane_owners=0,default_legacy_settings_exact=0)

    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)

    for archive in FILES:
        loaded=prepared(archive,zstd)
        data,records,features,member,members,bindings=loaded
        original=copy.deepcopy((features,bindings))
        candidates=[f for f in features if f.get('class_guid')==MIRROR]
        if not candidates:candidates=[features[0]]
        qualified=[qualify_mirror_cache_sources(*loaded,f) for f in candidates]
        rows=[r for r in qualified if r is not None]
        check(archive+' caller metadata and binding dictionaries unchanged',(features,bindings)==original)
        sample=dict(archive=archive,archive_sha256=sha(ROOT/archive),member=member,expected_sources=rows)
        if archive in CONTROLS:
            check(archive+' recognized outside family produces no source row',not rows)
            sample['empty_control']=True
            samples.append(sample)
            continue
        check(archive+' exactly one qualified native source',len(rows)==1)
        row=rows[0];feature=next(f for f in features if f['object_id']==row['feature_object_id'])
        sources=row['source_native_body_object_ids'];results=row['result_anchors']
        check(archive+' explicit count/source/result uniqueness',len(sources)==row['settings']['input_count']==len(results)
            and len(set(sources))==len(sources) and len({r['native_body_object_id'] for r in results})==len(results)
            and not set(sources)&{r['native_body_object_id'] for r in results})
        check(archive+' unique source-owned and result-owned anchors',all(
            p['source_anchor']['native_body_object_id']==nid and p['source_anchor']['source_owner_object_id']!=row['feature_object_id']
            for p,nid in zip(row['source_provenance'],sources))
            and all(a['source_owner_object_id']==row['feature_object_id'] for a in results))
        check(archive+' literal controller naming pair and two typed keys',row['stored_instance_key_pair'][0]==2
            and row['stored_instance_key_pair'][1]>0 and {e['stored_element_key'] for e in row['element_records']}=={1,2}
            and len({e['object_id'] for e in row['element_records']})==2)
        primary={r.object_id:r for r in records if r.is_primary}
        for element in row['element_records']:
            rec=primary[element['object_id']];payload=data[rec.body:rec.end]
            check(archive+' exact element payload '+str(rec.object_id),len(payload)==17
                and payload.hex()==element['native_record']['payload_hex']
                and struct.unpack_from('<I',payload,2)[0]==element['stored_element_key']
                and reference(payload,6)==element['control_record_object_id'])
        cp=row['component_provenance'];component=cp['component_object_id']
        check(archive+' shared component is supported by every BODY and fresh owner scope',component==3
            and all(p['body_properties']['component_object_id']==component==p['collection']['component_object_id'] for p in cp['body_ownership'])
            and all(o['component_object_id']==component and 'component_scope_object_id' in o for o in cp['dependency_scopes']))
        plane=row['selected_plane'];kind=plane['kind']
        if kind=='OriginConstructionPlane':
            counts['origin_plane_owners']+=1
            route=cp['selected_plane_component_route']
            check(archive+' selected origin plane occurs once in typed component container',route['component_object_id']==component
                and route['origin_member_object_ids'].count(plane['native_plane_object_id'])==1
                and plane['native_proof']['component_route']==route)
        elif kind=='StoredConstructionPlane':
            counts['stored_Offset_plane_owners']+=1
            route=cp['selected_plane_component_route'];definition=plane['native_proof']['definition']
            check(archive+' custom stored plane has full Offset definition/repeated collection',definition['definition_kind']=='Offset'
                and plane['origin']==definition['cached_geometry']['origin_cm']
                and plane['native_plane_object_id']==definition['plane_object_id']
                and route['stored_member_object_ids']==route['repeated_member_object_ids']==[plane['native_plane_object_id']]
                and route['component_object_id']==component)
        else:
            counts['named_face_plane_owners']+=1
            face=plane['native_proof']
            check(archive+' face support has separately qualified native BODY/blob route',kind=='NamedBRepFaceCache'
                and plane['history_blob_member']==face['history_blob_member']
                and plane['source_body_binding']==face['source_body_binding']
                and any(p['native_body_object_id']==plane['native_body_object_id'] for p in cp['body_ownership'])
                and face['cache_plane']['raw_origin']==plane['origin'])
        check(archive+' opaque API/current/history identities not promoted',all(row[k] is None for k in
            ('API_handle_identity','current_source_identity','persistent_source_identity','qualified_historical_state')))
        if archive in legacy:
            check(archive+' fresh complete settings match unchanged legacy reader golden',row['settings']==legacy[archive])
            counts['default_legacy_settings_exact']+=1
        if archive.endswith('/mirror_two_features.f3d'):
            check('Two Feature descriptor order is explicit and separate from result order',
                [p['input_descriptor']['descriptor_object_id'] for p in row['source_provenance']]==[400,404]
                and [p['input_descriptor']['source_feature_object_id'] for p in row['source_provenance']]==[322,243]
                and sources==[354,275] and [a['native_body_object_id'] for a in results]==[436,441])
            # The old default reader still deliberately rejects two Feature inputs.
            rec=primary[feature['object_id']]
            try:
                decode_mirror_modes(data,records,data[rec.body:rec.end],feature,
                    known_construction_entities(data,records,features),features)
            except ValueError as error:
                check('Default single-Feature restriction remains exact',str(error)=='Only captured single-Extrude Mirror feature input supported')
                sample['unchanged_default_count_rejection']=str(error)
            else:raise AssertionError('Default two Feature opt-in leaked')
        counts['source_BODY_routes']+=len(sources);counts['owned_result_anchors']+=len(results)
        saved[archive]=loaded,feature,row
        samples.append(sample)

    def rejected(label,case,changed_data=None,changed_records=None):
        loaded,feature,_=saved[case]
        d,rs,fs,m,ms,bb=loaded
        if changed_data is not None:ms={**ms,m:changed_data}
        try:
            qualify_mirror_cache_sources(changed_data if changed_data is not None else d,
                changed_records if changed_records is not None else rs,fs,m,ms,bb,feature)
        except (ValueError,KeyError,IndexError,TypeError,struct.error) as error:
            guards.append(dict(guard=label,rejected=True,reason=str(error)))
            check(label,True)
        else:raise AssertionError(label)

    base='remainingbodyinputs-7b3357274e85/mirror_two_features.f3d'
    loaded,feature,row=saved[base];d,rs,fs,m,ms,bb=loaded;p={r.object_id:r for r in rs if r.is_primary}
    rejected('Duplicate primary BODY cannot be overwritten by ownership maps',base,changed_records=rs+[p[row['source_native_body_object_ids'][0]]])
    source_leaf=row['source_provenance'][0]['input_descriptor']['terminal_object_id']
    changed=bytearray(d);struct.pack_into('<Q',changed,p[source_leaf].body+2,row['feature_object_id'])
    rejected('Feature selector leaf self-reference',base,changed_data=bytes(changed))
    anchor=row['result_anchors'][0]
    changed=bytearray(d);struct.pack_into('<Q',changed,p[anchor['object_id']].body+92,row['source_provenance'][0]['source_anchor']['source_owner_object_id'])
    rejected('Owned result anchor redirected to source owner',base,changed_data=bytes(changed))
    control=row['native_controller_proof']['object_id']
    changed=bytearray(d);struct.pack_into('<Q',changed,p[control].body+54,3)
    rejected('Literal native mirrored-element pair disagrees',base,changed_data=bytes(changed))
    nid=row['source_native_body_object_ids'][0];rec=p[nid]
    changed=bytearray(d);struct.pack_into('<Q',changed,rec.end-10,22)
    rejected('BODY footer no longer reciprocates its counted component collection',base,changed_data=bytes(changed))
    container=row['component_provenance']['selected_plane_component_route']['container_object_id'];rec=p[container]
    changed=bytearray(d);struct.pack_into('<Q',changed,rec.end-10,nid)
    rejected('Selected origin container component disagrees with BODY scopes',base,changed_data=bytes(changed))
    custom='bodyselections-62e42366c722/mirror_two_bodies_plane.f3d'
    loaded,feature,row=saved[custom];d,rs,fs,m,ms,bb=loaded;p={r.object_id:r for r in rs if r.is_primary}
    cid=row['component_provenance']['selected_plane_component_route']['collection_object_id'];rec=p[cid]
    payload=d[rec.body:rec.end];count=struct.unpack_from('<I',payload,2)[0];repeat=len(payload)-15-11*count
    changed=bytearray(d);struct.pack_into('<Q',changed,rec.body+repeat+5,44)
    rejected('Custom stored plane repeated membership redirected to origin plane',custom,changed_data=bytes(changed))
    return dict(scope=SCOPE,samples=samples,validation=dict(positive_owners=7,complete_empty_controls=5,
        **counts,focused_checks=len(checks),malformed_guards=len(guards),geometry_fits=0,main_calls=0,live_API_calls=0),
        checks=checks,malformed_guards=guards,
        source_sha256={n:sha(ROOT/n) for n in ('decode_mirror_cache_sources.py','validate_mirror_cache_sources.py',
            'decode_mirror_modes.py','decode_body_selections.py','decode_body_properties.py','decode_dependencies.py',
            'decode_assembly.py','decode_mirror_face_planes.py','decode_plane_definitions.py')},
        integration=dict(callable='qualify_mirror_cache_sources(data,records,features,member,members,body_blob_bindings,feature)',
            goldens='samples[].expected_sources is the full factory-row list, empty for five controls; reflection native_source_provenance must equal a full row',
            no_fit='Source, anchors, selected plane and component only; reflection matrices and cache-name joins belong to their separate reader'),
        limitations=['No geometry fits or coordinate-based source/result pairing occurs in this native factory',
            'Literal result-anchor order and selected source-descriptor order are separate; the two-Feature contrast reverses source BODY order',
            'Selected native Offset geometry comes from its fully parsed owned stored definition, never the requested offset',
            'Origin/support/source/result component equality is proved by native membership/backlinks and fresh dependency scopes; no occurrence solver or current state claim',
            'Native plane settings remain unchanged, including plane/plane_geometry None for the face support; its qualified initial-cache evidence is separate'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library')
    parser.add_argument('--output',default='mirror-cache-source-decoding.json')
    args=parser.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd)
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['validation'],sort_keys=True))
