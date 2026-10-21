"""Pinned full-output invariance and focused ASM EDGE chain byte evidence.

The default main-reader cache remains exact; recovery is separately demonstrated
through the explicitly invoked generic naming reader on seven actual blobs.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags,encode_generic_tag_payload
from decode_stitch_hint_attributes import decode_stitch_hint_attribute
from fusion_archive import read_members
from validate_history_cache_integration import baseline_outputs,differences

ROOT=Path(__file__).resolve().parent
BASELINE='593bc5e'
CACHE=Path('/private/tmp/fusion-edge-chain-outputs.json')
FILES=(
 'partinglinedrafts-c4d07c76fcd5/fixed_seven.f3d',
 'partinglinedrafts-c4d07c76fcd5/fixed_three.f3d',
 'partinglinedrafts-c4d07c76fcd5/moving_both_three.f3d',
 'patchcontinuity-b9b0be85a281/brep_curvature.f3d',
 'patchcontinuity-b9b0be85a281/brep_free.f3d',
 'patchcontinuity-b9b0be85a281/brep_tangent.f3d',
 'draftmodes-9b1a30f74aed/single.f3d',
 'surfacetools-856ca50cf4c7/patch_circle.f3d',
 'meshcontrasts-10c2557c91a3/stl_centimeter.f3d',
 'assembly-acc48a9dc05d/assembly.f3d')
REPORTS=('draft-no-merge-attribute-decoding.json','stitch-hint-attribute-decoding.json')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def validate(zstd,saved_path=None):
    source_cache=saved_path if saved_path is not None else (CACHE if CACHE.is_file() else None)
    if source_cache is not None:
        raw=source_cache.read_bytes();saved=json.loads(raw)
        assert saved['baseline_commit']==BASELINE and saved['files']==list(FILES),'Cache manifest/revision differs'
        before,current=saved['before'],saved['after'];main_runs=0
    else:
        from decode_basics import decode_basics
        before=baseline_outputs(list(FILES),zstd,revision=BASELINE)
        current=[decode_basics(ROOT/name,zstd) for name in FILES];main_runs=10
    assert len(before)==len(current)==len(FILES)==10
    report=dict(scope='Ten pinned saved default main-reader outputs remain exact against593bc5e; two separately invoked focused ASM owner-chain stages recover ten diagnostics with literal byte replay. No global coverage conclusion.',
        baseline_commit=BASELINE,files=list(FILES),full_output_checks=[],focused_chain_checks=[],duplicate_name_ambiguity=[],
        inputs=dict(saved_cache=str(source_cache) if source_cache is not None else None,
            saved_cache_sha256=hashlib.sha256(raw).hexdigest() if source_cache is not None else None,
            archive_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES},
            focused_report_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in REPORTS},
            source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
                'decode_asm_recipe_tags.py','decode_counted_asm_names.py','decode_stitch_hint_attributes.py',
                'validate_draft_no_merge_attributes.py','validate_stitch_hint_attributes.py','validate_edge_chain_integration.py')}),
        validation_command='python3 validate_edge_chain_integration.py --saved-outputs /private/tmp/fusion-edge-chain-outputs.json --zstd-library <libzstd path>')
    for filename,old,new in zip(FILES,before,current):
        suffix=Path(filename).parts
        for output in (old,new):
            assert Path(output['file']).parts[-len(suffix):]==suffix,(filename,'Cache filename/order mismatch')
            members=[s['member'] for s in output['streams']]
            assert len(members)==len(set(members)),(filename,'Duplicate cached native stream')
        assert new==old,(filename,'Unexpected default main-reader change',differences(old,new))
        assert digest(old)==digest(new)
        report['full_output_checks'].append(dict(archive=filename,all_fields_exact=True,
            unchanged_output_sha256=digest(new),difference_paths=[],
            ASM_geometry_placement_feature_controls_and_all_diagnostics_exact=True))
    draft=json.loads((ROOT/REPORTS[0]).read_text());patch=json.loads((ROOT/REPORTS[1]).read_text())
    assert draft['baseline_commit']==patch['historical_baseline']==BASELINE
    assert draft['counts']['new_head_chains']==draft['counts']['recovered_diagnostics']==6
    assert patch['summary']['target_initial_chain_diagnostics_recovered']==4
    # The recorded current source hashes qualify the frozen Draft report. Patch
    # records its historical audit hash; no equality with a refreshed audit assumed.
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value for name,value in draft['source_sha256'].items())
    archives={};blobs={};decoded={};new_keys=set()
    def actual(archive,member,expected_sha):
        assert archive in FILES
        if archive not in archives:archives[archive]=read_members(ROOT/archive,zstd)
        key=archive,member
        if key not in blobs:
            blob=archives[archive][member];assert hashlib.sha256(blob).hexdigest()==expected_sha
            parsed=inspect_asm(blob);assert parsed['complete_token_stream']
            blobs[key]=(blob,parsed)
            decoded[key]=decode_asm_generic_tags(blob,parsed=parsed,allow_fpm_tracking=True)
        else:assert hashlib.sha256(blobs[key][0]).hexdigest()==expected_sha
        return blobs[key][0],blobs[key][1],decoded[key]
    draft_goldens={(r['archive'],r['member']):r['expected_decoded'] for r in draft['blobs']}
    for row in draft['new_head_chains']:
        blob,parsed,summary=actual(row['archive'],row['member'],row['blob_sha256'])
        assert summary==draft_goldens[row['archive'],row['member']]
        records=parsed['records'];marker=records[row['no_merge_record_index']];generic=records[row['generic_record_index']]
        owner=records[row['owner_edge_record_index']]
        assert owner['name']=='edge' and marker['name']=='no_merge_attribute-st-attrib'
        assert owner['tokens'][0]['value']==marker['index']
        assert marker['tokens']==row['no_merge_header_tokens'] and generic['tokens'][:5]==row['generic_header_tokens']
        marker_bytes=b''.join(bytes([t['tag']])+struct.pack('<q',t['value']) for t in marker['tokens'])
        assert marker_bytes.hex()==row['no_merge_header_payload_hex']
        assert marker_bytes==blob[marker['tokens'][0]['offset']:marker['end_offset']-1]
        tag=next(t for t in summary['tags'] if t['attribute_record_index']==generic['index'])
        assert tag==row['shared_generic_tag']
        assert encode_generic_tag_payload(tag)==blob[tag['payload_offset']:tag['payload_end_offset']]
        assert tag['owner_attribute_chain']==[marker['index'],generic['index']]
        key=row['archive'],row['member'],generic['index'];assert key not in new_keys;new_keys.add(key)
        report['focused_chain_checks'].append(dict(archive=row['archive'],member=row['member'],
            family='NoMergeHead_GenericTail',generic_attribute_record_index=generic['index'],
            owner_edge_record_index=owner['index'],owner_attribute_chain=tag['owner_attribute_chain'],
            exact_marker_header_and_counted_name_replays=True,focused_summary_exact=True))
    for row in patch['samples']:
        blob,parsed,summary=actual(row['archive'],row['member'],row['blob_sha256'])
        assert summary==row['expected_generic_reader']
        evidence=row['owner_chain_evidence'];hint=parsed['records'][evidence['attribute_record_index']]
        assert decode_stitch_hint_attribute(hint,parsed['records'])==evidence
        for value,start,end in (('record_hex','record_offset','record_end_offset'),
            ('record_fields_hex','record_fields_offset','record_fields_end_offset'),
            ('numeric_payload_hex','numeric_payload_offset','numeric_payload_end_offset')):
            assert bytes.fromhex(evidence[value])==blob[evidence[start]:evidence[end]]
        tag=row['new_generic_tag'];assert tag in summary['tags']
        assert encode_generic_tag_payload(tag)==blob[tag['payload_offset']:tag['payload_end_offset']]
        key=row['archive'],row['member'],tag['attribute_record_index'];assert key not in new_keys;new_keys.add(key)
        report['focused_chain_checks'].append(dict(archive=row['archive'],member=row['member'],
            family='GenericHead_StitchHintTail',generic_attribute_record_index=tag['attribute_record_index'],
            owner_edge_record_index=evidence['owner_record_index'],owner_attribute_chain=evidence['owner_attribute_chain'],
            exact_hint_record_header_numeric_and_counted_name_replays=True,focused_summary_exact=True,
            raw_hint_payload_doubles=evidence['stored_payload_doubles'],payload_double_meanings=None))
    assert len(new_keys)==10 and len(blobs)==7
    for key,summary in decoded.items():
        target_rows=[r for r in draft['new_head_chains'] if (r['archive'],r['member'])==key]
        if not target_rows:continue
        target=target_rows[0]['shared_generic_tag']
        candidates=[t for t in summary['tags'] if t['payload_hex']==target['payload_hex']]
        assert len(candidates)==2 and len({t['owner_record_index'] for t in candidates})==2
        report['duplicate_name_ambiguity'].append(dict(archive=key[0],member=key[1],
            stored_terms=target['terms'],matching_attribute_record_indices=[t['attribute_record_index'] for t in candidates],
            matching_owner_edge_record_indices=[t['owner_record_index'] for t in candidates],
            selected_source_owner_record_index=None,persistent_edge_identity=None,
            scope='Two distinct typed EDGE owners retain identical exact counted naming payload; no owner selected by geometry/order or by opaque component304'))
    assert len(report['duplicate_name_ambiguity'])==3
    report['focused_prior_controls']=dict(draft_previous_generic_dictionaries_exact=draft['counts']['previous_generic_tags_exact'],
        draft_old_tail_chain_controls=draft['counts']['old_tail_chains'],draft_malformed_guards=len(draft['guards']),
        patch_previous_generic_dictionaries_exact=patch['summary']['old_generic_tag_dictionaries_exact'],
        patch_Free_and_old_no_merge_controls=patch['summary']['Free_and_no_merge_control_blobs'],
        patch_malformed_guards=len(patch['malformed_guards']),
        scope='Frozen focused reports retain independently validated controls; this integration does not rerun their broader fixture sets')
    # A separately refreshed pure audit is qualified against the same saved
    # archive manifest; this reads JSON evidence, never reruns the corpus.
    audit_path=ROOT/'asm-attribute-frontier-current.json'
    audit_raw=audit_path.read_bytes();audit=json.loads(audit_raw)
    old_audit_raw=subprocess.check_output(['git','show',BASELINE+':asm-attribute-frontier-current.json'],cwd=ROOT)
    old_audit=json.loads(old_audit_raw)
    old_keys={(e['file'],e['member'],e['attribute_record_index']) for g in old_audit['unresolved_groups'] for e in g['entries']}
    assert old_keys==new_keys and old_audit['unresolved_diagnostic_count']==10
    assert audit['unresolved_diagnostic_count']==0 and audit['unresolved_groups']==[] and audit['frontier_summary']==[]
    assert audit['blobs_with_initial_attribute_diagnostics']==0
    raw_keys=('archive_count','blob_count','initial_custom_attribute_count','custom_definition_counts_by_section',
        'custom_definition_owner_kind_inventory','attribute_entity_record_kind_counts_by_section',
        'raw_initial_generic_counted_extents','initial_generic_payload_framing','nested_metadata_payload_framing',
        'namespace_scope','read_or_framing_failure_count','failure_stage_counts',
        'inventory_classification_errors','read_or_framing_failures')
    assert all(audit[k]==old_audit[k] for k in raw_keys)
    assert audit['archive_count']==627 and audit['blob_count']==1091 and audit['initial_custom_attribute_count']==33616
    for k in ('archive_manifest','archive_manifest_sha256','archive_discovery'):
        assert audit['provenance'][k]==old_audit['provenance'][k]
    assert audit['read_or_framing_failure_count']==0 and not audit['inventory_classification_errors']
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value
        for name,value in audit['provenance']['reader_source_sha256'].items())
    assert 'decode_stitch_hint_attributes.py' in audit['provenance']['reader_source_sha256']
    expected=copy.deepcopy(old_audit['initial_attribute_classification_counts'])
    assert expected.pop('Unresolved')==10;expected['OwnedGenericName']+=10
    assert audit['initial_attribute_classification_counts']==expected
    expected=copy.deepcopy(old_audit['initial_definition_framing_status_counts'])
    assert expected['generic_tag_attrib_def'].pop('Unresolved')==10
    expected['generic_tag_attrib_def']['OwnedGenericName']+=10
    assert audit['initial_definition_framing_status_counts']==expected
    expected=copy.deepcopy(old_audit['owned_initial_generic_names'])
    expected['term_count_distribution']['1']+=10;expected['component_count_distribution_per_term']['1']+=10
    assert audit['owned_initial_generic_names']==expected
    def inventory_key(row):
        return row['definition_name'],row['owner_kind'],row['classification'],row['term_count'],tuple(row['component_counts_in_stored_order'])
    expected={inventory_key(r):copy.deepcopy(r) for r in old_audit['counted_owner_framing_inventory']}
    assert expected.pop(('generic_tag_attrib_def','edge','Unresolved',1,(1,)))['count']==10
    expected['generic_tag_attrib_def','edge','OwnedGenericName',1,(1,)]['count']+=10
    assert {inventory_key(r):r for r in audit['counted_owner_framing_inventory']}==expected
    assert len(old_audit['blobs'])==len(audit['blobs'])==1091
    for old_blob,new_blob in zip(old_audit['blobs'],audit['blobs']):
        expected=copy.deepcopy(old_blob)
        count=sum(archive==old_blob['file'] and member==old_blob['member'] for archive,member,_ in new_keys)
        if count:
            assert expected['initial_attribute_classification_counts'].pop('Unresolved')==count
            expected['initial_attribute_classification_counts']['OwnedGenericName']+=count
            expected['unresolved_count']=0
        assert expected==new_blob,(old_blob['file'],old_blob['member'],'Unexpected pure-audit blob change')
    report['pure_audit_followup']=dict(audit_file='asm-attribute-frontier-current.json',
        audit_sha256=hashlib.sha256(audit_raw).hexdigest(),baseline_audit_sha256=hashlib.sha256(old_audit_raw).hexdigest(),
        saved_archive_manifest_exact=True,archive_manifest_sha256=audit['provenance']['archive_manifest_sha256'],
        saved_archives=627,saved_blobs=1091,initial_custom_attributes=33616,
        raw_inventories_and_blob_hashes_exact=True,old_chain_diagnostics=10,current_chain_diagnostics=0,
        exact_recovered_diagnostic_keys=sorted([list(key) for key in new_keys]),
        current_owned_generic_names=12674,current_validated_other_definitions=20942,
        read_framing_or_classification_errors=0,audit_reader_source_hashes_current=True,
        scope='Only this627-archive/1091-blob initial attribute framing frontier; no complete-format, persistent identity or future-archive coverage claim')
    report['summary']=dict(pinned_saved_files=10,recent_capture_files=6,legacy_full_output_controls=4,
        full_main_outputs_exact=10,unexpected_default_output_changes=0,
        focused_new_chain_diagnostics_recovered=10,draft_no_merge_head_chains=6,patch_stitch_hint_tail_chains=4,
        actual_target_blobs_replayed=7,explicit_duplicate_name_ambiguity_blobs=3,
        current_main_reader_runs=main_runs,live_API_calls=0)
    report['limits']=[
        'Full default main-reader outputs remain exact; the ten recoveries belong to the explicitly invoked ASM attribute reader and focused reports, not newly changed default main summaries.',
        'Initial typed EDGE owner/header/next/previous links and literal bytes only. no_merge class spelling and stitch_hint raw doubles do not establish solver or merge/stitch behavior.',
        'Opaque name components are not native object IDs; duplicate naming candidates are retained without selected or persistent edge identity, geometry matching or qualified history state.',
        'The separately refreshed initial attribute audit is qualified only for its unchanged627-archive manifest. Its ten-to-zero framing diagnostic result does not imply complete format decoding, topology identity or support for unobserved archives.']
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saved-outputs',type=Path);parser.add_argument('--zstd-library')
    parser.add_argument('--output',type=Path,default=ROOT/'edge-chain-integration.json');args=parser.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd,args.saved_outputs);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
