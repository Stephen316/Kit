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
PARAMETER_CAPTURES=tuple('parameteridentity-8fc83529b236/'+name+'.f3d' for name in
                       ('01_literal','02_alpha_reference','03_bravo_reference','04_literal_return'))
COLOR_CAPTURES=('componentcolorcontrast-775cb30dfc1e/known_component_color.f3d',)
FOLLOWUP_CAPTURES=PARAMETER_CAPTURES+COLOR_CAPTURES
PRIOR561=dict(manifest_sha256='5f123da45456a1310292ff16004abd6a07509c931bd2ac761f2ce68978eef660',
    parser_sha256='9fcfd976fb1437bec36d106c3c9f7c3240f57c4287d3ef74956e09967f0f7cd7',
    saved_archives=561,Design_asset_occurrences=561,typed_registry_records=596,
    decoded_registries=499,decoded_populated_registries=444,decoded_empty_registries=55,
    unresolved_registries=97,scope='Frozen original561-file census before reverse-only parser admission and four later parameter-identity controls')


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
            'Exact replay and table-layout qualification establish stored associations only. Reverse-only layouts do not acquire a fabricated forward map or reciprocity claim; persistent topology identity, dependency edges, lifecycle and ASM association remain outside scope.',
            'Identical numeric owner IDs and keys across different assets/files are separate scopes. They are not deduplicated or promoted to global identities.',
            'Only variants admitted by the shared parser count as decoded. Remaining reverse-table/footer failures retain exact source bodies and stay explicit frontier cases.',
            'This census makes no live Fusion calls and does not run feature, geometry, ASM, solve or native-writing pipelines.'])
    totals=Counter();classes=Counter();reverse_only_classes=Counter();assets=Counter();shapes=Counter();footer=Counter();no_registry=[]
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
                    is_reverse_only=registry.get('table_layout')=='StoredReverseOnly'
                    if is_reverse_only:
                        assert not forward and reverse and registry.get('reciprocity_status')=='ForwardTableAbsent'
                        assert registry['registry_is_empty'] is False
                        assert len(reverse)==len(registry['key_to_owner'])
                        totals['decoded_reverse_only_registries']+=1
                        totals['reverse_only_naming_key_rows']+=len(reverse)
                    else:
                        assert forward==reverse and len(forward)==len(registry['key_to_owner'])
                    truly_empty=not registry['owner_to_keys'] and not registry['key_to_owner']
                    assert registry['registry_is_empty']==truly_empty
                    raw_owner_fields=[]
                    for owner in registry['owner_to_keys']:
                        offset=owner['stored_owner_field_offset']
                        assert struct.unpack_from('<Q',data,offset)[0]==owner['native_owner_object_id']
                        classes[owner['native_owner_class_guid']]+=1
                        raw_owner_fields.append(dict(table='owner_to_keys',absolute_offset=offset,encoding='raw_u64_schema_field',native_owner_object_id=owner['native_owner_object_id']))
                    for owner in registry['key_to_owner']:
                        offset=owner['stored_owner_field_offset']
                        assert struct.unpack_from('<Q',data,offset)[0]==owner['native_owner_object_id']
                        target_owner=by[owner['native_owner_object_id']]
                        assert target_owner.class_guid==owner['native_owner_class_guid']
                        if is_reverse_only:reverse_only_classes[target_owner.class_guid]+=1
                    pos=registry['container_reference_offset'];native_ref=data[pos:pos+11]
                    assert native_ref[:1]==b'\1' and native_ref[9:]==b'\0\0' and struct.unpack_from('<Q',native_ref,1)[0]==registry['registry_container_object_id']
                    back=registry['container_backlink_offset'];backref=data[back:back+11]
                    assert backref[:1]==b'\1' and backref[9:]==b'\0\0' and struct.unpack_from('<Q',backref,1)[0]==registry['object_id']
                    owners=len(registry['owner_to_keys']);keys=len(registry['key_to_owner'])
                    layout='StoredReverseOnly' if is_reverse_only else ('StoredEmpty' if truly_empty else 'ReciprocalPopulated')
                    shape=(owners,keys,tuple(sorted(len(x['naming_keys']) for x in registry['owner_to_keys'])),layout)
                    shapes[shape]+=1;footer[registry['stored_footer_hex']]+=1
                    totals['decoded_registries']+=1;totals['owner_rows']+=owners;totals['naming_key_rows']+=keys
                    if not is_reverse_only:totals['decoded_empty_registries' if truly_empty else 'decoded_populated_registries']+=1
                    totals['scoped_native_owner_identities']+=len({x['native_owner_object_id'] for x in registry['owner_to_keys']}|
                                                               {x['native_owner_object_id'] for x in registry['key_to_owner']})
                    totals['raw_u64_owner_fields']+=owners+keys;totals['typed_footer_references']+=1;totals['typed_container_backlinks']+=1
                    totals['exact_payload_byte_replays']+=1;totals['replayed_payload_bytes']+=len(replay)
                    target['registries'].append(dict(object_id=registry['object_id'],registry_container_object_id=registry['registry_container_object_id'],
                        payload_offset=r.body,payload_byte_count=len(body),payload_sha256=hashlib.sha256(body).hexdigest(),
                        exact_payload_replay_matches=True,registry_is_empty=truly_empty,owner_row_count=owners,key_row_count=keys,
                        audit_table_layout=layout,
                        reciprocity_evidence=('ForwardTableAbsent; actual second-table associations retained without fabricating a forward table' if is_reverse_only
                                              else 'Exact equality of both stored owner/key association sets'),
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
    report['native_owner_class_distribution_scope']='Actual forward-table owner rows only; the independently stored reverse-only owner associations have their separate class distribution below.'
    report['reverse_only_native_owner_class_distribution']=dict(sorted(reverse_only_classes.items()))
    report['registry_shape_distribution']=[dict(owner_count=a,stored_second_table_key_count=k,key_counts_per_owner=list(b),audit_table_layout=layout,registry_count=n)
                                            for (a,k,b,layout),n in sorted(shapes.items())]
    report['stored_footer_distribution']=dict(sorted(footer.items()))
    report['Design_assets_without_registry']=no_registry
    report['actual_new_capture_files']=[dict(manifest_entry=next((m for m in manifest if m['file']==name),None),
        registry_census=next((f for f in report['files'] if f['file']==name),None)) for name in NEW_CAPTURES]
    baseline_manifest=[m for m in manifest if m['file'] not in FOLLOWUP_CAPTURES]
    baseline_hash=hashlib.sha256(json.dumps(baseline_manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    original_counts=Counter();parameter_counts=Counter();color_counts=Counter()
    for f in report['files']:
        target=(parameter_counts if f['file'] in PARAMETER_CAPTURES else
                color_counts if f['file'] in COLOR_CAPTURES else original_counts)
        target['saved_archives']+=1
        for a in f['Design_assets']:
            target['Design_asset_occurrences']+=1;target['unresolved_registries']+=len(a['unresolved'])
            for r in a['registries']:
                target['decoded_registries']+=1
                target[r['audit_table_layout']]+=1
    report['original561_corpus_comparison']=dict(historical_results=PRIOR561,
        current_reader_original_archive_subset=dict(original_counts),
        original_file_bytes_and_paths_unchanged=baseline_hash==PRIOR561['manifest_sha256'],
        current_original_archive_subset_manifest_sha256=baseline_hash,
        scope='Current parser results and original historical results remain separate; the97 formerly rejected records now have actual reverse-only rows. All five later exports (four parameter controls and one controlled component-color capture) are excluded from this original561 corpus comparison.')
    report['four_added_parameter_identity_controls']=dict(files=[dict(manifest_entry=next((m for m in manifest if m['file']==name),None),
        registry_census=next((f for f in report['files'] if f['file']==name),None)) for name in PARAMETER_CAPTURES],
        counts=dict(parameter_counts),
        all_actual_rows_are_old_compatible_empty_layouts=(parameter_counts['saved_archives']==4 and parameter_counts['decoded_registries']==parameter_counts['StoredEmpty']==4
                                                         and not parameter_counts['unresolved_registries']),
        scope='Four actual same-document parameter-identity exports added after the frozen561-file census; no expression-dependency interpretation is made by this registry audit')
    report['one_added_component_color_control']=dict(files=[dict(manifest_entry=next((m for m in manifest if m['file']==name),None),
        registry_census=next((f for f in report['files'] if f['file']==name),None)) for name in COLOR_CAPTURES],
        counts=dict(color_counts),
        actual_row_is_old_compatible_empty_layout=(color_counts['saved_archives']==color_counts['decoded_registries']==color_counts['StoredEmpty']==1
                                                 and not color_counts['unresolved_registries']),
        scope='One actual owned-import componentColor setter/getter export, separately classified from the four parameter controls. This registry census makes no component-color interpretation.')
    report['five_added_followup_captures']=dict(files=list(FOLLOWUP_CAPTURES),
        counts={key:parameter_counts[key]+color_counts[key] for key in sorted(parameter_counts.keys()|color_counts.keys())},
        scope='Aggregate of the two explicitly separated later-capture groups; all five files are excluded from the frozen561-file manifest.')
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
