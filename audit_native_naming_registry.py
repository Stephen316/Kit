"""Pure metadata-indexed native naming-registry census; no full model decoding.

The shared parser owns the schema. This audit replays its exact output against
source bodies and independently counts scoped rows, owner fields and footer
references. No registry key is treated as a native or persistent entity ID.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import time

from decode_native_naming_registry import decode_native_naming_registry,encode_native_naming_registry,REGISTRY
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
NEW_CAPTURES=('namedvertexprobe-8d81619f74e6/construction_polynomial_vertex0.f3d',
              'namedvertexprobe-8d81619f74e6/scale_rational_vertex2.f3d')


def audit(root=ROOT,zstd_library=None):
    root=Path(root).resolve();started=time.monotonic()
    source_names=('audit_native_naming_registry.py','decode_native_naming_registry.py','fusion_metadata.py','fusion_archive.py','decode_sketch.py')
    source_hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in source_names}
    files=sorted(root.glob('*/*.f3d'))
    manifest=[dict(file=str(p.relative_to(root)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),byte_count=p.stat().st_size) for p in files]
    manifest_bytes=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
    report=dict(scope='Pure read-only census of every saved one-level capture archive and every native Design asset member; shared registry parser plus exact typed-body replay, no decode_basics/full model pipeline',
        provenance=dict(root=str(root),manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),source_sha256=source_hashes,
                        archive_glob='*/*.f3d',all_recursive_archive_paths_agree=files==sorted(root.rglob('*.f3d'))),
        schema_ownership='decode_native_naming_registry.py is the only schema parser; this audit does not copy a second registry decoder',
        identity_scope='Native owner identities are qualified by file/asset/registry. Naming keys are opaque registry literals, and census totals count scoped rows rather than globally unique numeric IDs.',
        owner_encoding_scope='Forward owner fields and reverse owner fields are raw little-endian u64 schema fields, resolved to typed primary records. They are not11-byte reference encodings. The footer separately contains an11-byte tag1/u64/two-zero reference to the native history container, whose native backlink is also framed.',
        file_manifest=manifest,files=[],archive_failures=[],record_failures=[],
        actual_new_capture_files=[],validation={},limitations=[
            'Exact replay and table reciprocity establish the captured native registry schema, not persistent topology identity, dependency edges, lifecycle or ASM association.',
            'Identical numeric owner IDs and keys across different assets/files are separate scopes. They are not deduplicated or promoted to global identities.',
            'Only variants admitted by the shared parser count as decoded. Remaining reverse-table/footer failures retain exact source bodies and stay explicit frontier cases.',
            'This census makes no live Fusion calls and does not run feature, geometry, ASM, solve or native-writing pipelines.'])
    totals=Counter();classes=Counter();assets=Counter();shapes=Counter();footer=Counter();no_registry=[]
    for p,entry in zip(files,manifest):
        relative=entry['file'];row=dict(file=relative,sha256=entry['sha256'],Design_assets=[])
        try:members=read_members(p,zstd_library)
        except (ValueError,RuntimeError,OSError) as error:
            report['archive_failures'].append(dict(file=relative,reason=str(error)));report['files'].append(row);continue
        for member,data in members.items():
            if not member.endswith('/FusionDesignSegmentType1/BulkStream.dat'):continue
            asset=member.rsplit('/FusionDesignSegmentType1/',1)[0];assets[asset]+=1;totals['Design_asset_occurrences']+=1
            try:
                records,index=design_records(data,members.get(member.replace('BulkStream.dat','MetaStream.dat')))
                result=decode_native_naming_registry(data,records)
                candidates=[r for r in records if r.is_primary and r.class_guid==REGISTRY]
                assert len(result['decoded'])+len(result['unresolved'])==len(candidates)
                totals['typed_registry_records']+=len(candidates)
                totals['Design_assets_with_registry_candidates']+=int(bool(candidates))
                target=dict(asset_scope=asset,member=member,source_Design_sha256=hashlib.sha256(data).hexdigest(),
                            indexed_record_count=len(records),typed_registry_record_count=len(candidates),registries=[],unresolved=[])
                by={r.object_id:r for r in records if r.is_primary}
                for error in result['unresolved']:
                    failed=by[error['object_id']];failed_body=data[failed.body:failed.end]
                    target['unresolved'].append(dict(error,source_payload_offset=failed.body,source_payload_byte_count=len(failed_body),
                        source_payload_sha256=hashlib.sha256(failed_body).hexdigest(),source_payload_hex=failed_body.hex(),
                        scope='Actual parser rejection and complete source body retained; no unproven alternate schema decoded by this audit'))
                if not candidates:no_registry.append(dict(file=relative,member=member))
                for registry in result['decoded']:
                    r=by[registry['object_id']];body=data[r.body:r.end]
                    replay=encode_native_naming_registry(registry)
                    assert replay==body
                    forward={(key,x['native_owner_object_id']) for x in registry['owner_to_keys'] for key in x['naming_keys']}
                    reverse={(x['naming_key'],x['native_owner_object_id']) for x in registry['key_to_owner']}
                    assert forward==reverse and len(forward)==len(registry['key_to_owner'])
                    raw_owner_fields=[]
                    for owner in registry['owner_to_keys']:
                        offset=owner['stored_owner_field_offset']
                        assert struct.unpack_from('<Q',data,offset)[0]==owner['native_owner_object_id']
                        classes[owner['native_owner_class_guid']]+=1
                        raw_owner_fields.append(dict(table='owner_to_keys',absolute_offset=offset,encoding='raw_u64_schema_field',native_owner_object_id=owner['native_owner_object_id']))
                    for owner in registry['key_to_owner']:
                        offset=owner['stored_owner_field_offset']
                        assert struct.unpack_from('<Q',data,offset)[0]==owner['native_owner_object_id']
                    pos=registry['container_reference_offset'];native_ref=data[pos:pos+11]
                    assert native_ref[:1]==b'\1' and native_ref[9:]==b'\0\0' and struct.unpack_from('<Q',native_ref,1)[0]==registry['registry_container_object_id']
                    back=registry['container_backlink_offset'];backref=data[back:back+11]
                    assert backref[:1]==b'\1' and backref[9:]==b'\0\0' and struct.unpack_from('<Q',backref,1)[0]==registry['object_id']
                    owners=len(registry['owner_to_keys']);keys=len(registry['key_to_owner'])
                    shape=(owners,tuple(sorted(len(x['naming_keys']) for x in registry['owner_to_keys'])))
                    shapes[shape]+=1;footer[registry['stored_footer_hex']]+=1
                    totals['decoded_registries']+=1;totals['owner_rows']+=owners;totals['naming_key_rows']+=keys
                    totals['decoded_empty_registries' if owners==0 else 'decoded_populated_registries']+=1
                    totals['raw_u64_owner_fields']+=owners+keys;totals['typed_footer_references']+=1;totals['typed_container_backlinks']+=1
                    totals['exact_payload_byte_replays']+=1;totals['replayed_payload_bytes']+=len(replay)
                    target['registries'].append(dict(object_id=registry['object_id'],registry_container_object_id=registry['registry_container_object_id'],
                        payload_offset=r.body,payload_byte_count=len(body),payload_sha256=hashlib.sha256(body).hexdigest(),
                        exact_payload_replay_matches=True,registry_is_empty=owners==0,owner_row_count=owners,key_row_count=keys,
                        owner_to_keys=registry['owner_to_keys'],key_to_owner=registry['key_to_owner'],
                        raw_forward_owner_field_evidence=raw_owner_fields,
                        typed_footer_reference=dict(absolute_offset=pos,encoded_hex=native_ref.hex(),target_object_id=registry['registry_container_object_id']),
                        typed_container_backlink=dict(absolute_offset=back,encoded_hex=backref.hex(),target_registry_object_id=registry['object_id']),
                        stored_footer_hex=registry['stored_footer_hex']))
                totals['unresolved_registries']+=len(result['unresolved'])
                row['Design_assets'].append(target)
            except (ValueError,IndexError,KeyError,AssertionError,struct.error) as error:
                report['record_failures'].append(dict(file=relative,member=member,reason=str(error)))
        report['files'].append(row)
    report['asset_scope_string_distribution']=dict(sorted(assets.items()))
    report['native_owner_class_distribution']=dict(sorted(classes.items()))
    report['registry_shape_distribution']=[dict(owner_count=a,key_counts_per_owner=list(b),registry_count=n) for (a,b),n in sorted(shapes.items())]
    report['stored_footer_distribution']=dict(sorted(footer.items()))
    report['Design_assets_without_registry']=no_registry
    report['actual_new_capture_files']=[dict(manifest_entry=next((m for m in manifest if m['file']==name),None),
        registry_census=next((f for f in report['files'] if f['file']==name),None)) for name in NEW_CAPTURES]
    end_hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in source_names}
    report['provenance']['source_files_unchanged_during_run']=source_hashes==end_hashes
    report['provenance']['ending_source_sha256']=end_hashes
    report['unresolved_reason_distribution']=dict(Counter(x['reason'] for f in report['files'] for a in f['Design_assets'] for x in a['unresolved']))
    report['validation']=dict(totals,saved_archives=len(files),archive_failures=len(report['archive_failures']),
        record_failures=len(report['record_failures']),Design_assets_without_registry=len(no_registry),
        namedvertex_new_capture_files_present=sum(x['manifest_entry'] is not None for x in report['actual_new_capture_files']),
        source_files_unchanged_during_run=source_hashes==end_hashes,new_live_API_calls=0,full_main_decodes=0,
        elapsed_seconds=time.monotonic()-started)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--zstd-library',default=None,help='Optional libzstd path; otherwise use system discovery')
    parser.add_argument('--output',type=Path,default=ROOT/'native-naming-registry-frontier.json')
    args=parser.parse_args();result=audit(args.root,args.zstd_library)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['validation'],sort_keys=True))
