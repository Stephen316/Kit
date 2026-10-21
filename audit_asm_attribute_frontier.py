"""Reproducible saved-corpus ASM custom attribute/name framing frontier.

Only initial geometry is qualified by the shared owner-chain reader. Trailing
custom attributes are inventoried literally in their geometry-ordinal namespace;
raw occurrence counts are not decoder coverage or historical identity claims.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import struct
import time

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, encode_generic_tag_payload
from decode_counted_asm_names import decode_counted_asm_name
from fusion_archive import read_members

ROOT = Path(__file__).resolve().parent
DISCOVERY = {
    'source': '/tmp/fusion-custom-framing-inventory.json (prior discovery; not read at runtime)',
    'archive_count': 559, 'blob_count': 959,
    'initial_custom_definition_counts': {'sketch_attrib_def':17175, 'Timestamp_attrib_def':1053,
        'generic_tag_attrib_def':11463, 'FPM_tracked_attrib_def':84, 'FDM_feature_attrib_def':19},
    'initial_generic_term_counts': {'1':11031, '2':364, '3':49, '4':13, '5':3, '6':2, '8':1},
    'initial_generic_component_counts': {'0':1101, '1':8108, '2':830, '3':1954},
}
SOURCES = ('audit_asm_attribute_frontier.py','asm_records.py','decode_asm_recipe_tags.py',
           'decode_counted_asm_names.py','decode_fdm_face_attributes.py','decode_sketch_attributes.py','fusion_archive.py')


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _counts(counter):
    return {str(k):v for k,v in sorted(counter.items(),key=lambda item:str(item[0]))}


def _raw_counted_extent(record):
    """Count literal extents only; this does not admit names/owners as decoded."""
    ts = record['tokens']
    def integer(index, low, high):
        t = ts[index]
        if t['kind'] != 'integer' or isinstance(t['value'], bool) or not low <= t['value'] <= high:
            raise ValueError('Raw naming count extent is not a bounded integer')
        return t['value']
    count, cursor, components, empty = integer(10, 1, 128), 11, [], 0
    for _ in range(count):
        length = integer(cursor, 0, 128)
        name = ts[cursor+1]
        if name['kind'] != 'string' or len(name['value'].encode('ascii')) != length:
            raise ValueError('Raw naming length does not match literal bytes')
        integer(cursor+2, 0, 0xffffffff)
        n = integer(cursor+3, 0, 128)
        for i in range(n):
            integer(cursor+4+i, -0x80000000, 0x7fffffff)
        integer(cursor+4+n, 0, 0)
        components.append(n); empty += int(length == 0)
        cursor += 5+n
    if cursor != len(ts):
        raise ValueError('Raw naming extents do not consume the payload')
    return count, components, empty


def audit(root=ROOT, zstd_library=None):
    root = Path(root)
    started = time.monotonic()
    source_hashes = {name:_hash((root/name).read_bytes())for name in SOURCES}
    revision = subprocess.run(['git','rev-parse','HEAD'],cwd=root,check=True,text=True,capture_output=True).stdout.strip()
    manifest, blobs, failures, diagnostics, inventory_errors = [], [], [], [], []
    section_definitions = defaultdict(Counter)
    section_owner_kinds = defaultdict(Counter)
    attribute_kinds = defaultdict(Counter)
    definition_status = defaultdict(Counter)
    payload_terms, payload_components, owned_terms, owned_components = Counter(),Counter(),Counter(),Counter()
    raw_terms, raw_components = Counter(), Counter()
    nested_terms, nested_components = Counter(), Counter()
    frontier_groups, framing_groups = defaultdict(list), {}
    totals = Counter()
    files = sorted(root.glob('*/*.f3d'))
    for path in files:
        relative = str(path.relative_to(root))
        archive_bytes = path.read_bytes()
        manifest.append({'file':relative,'byte_count':len(archive_bytes),'sha256':_hash(archive_bytes)})
        try:
            members = read_members(path,zstd_library)
        except Exception as error:
            failures.append({'file':relative,'stage':'archive_read','reason':str(error)})
            continue
        for member,blob in sorted(members.items()):
            if not member.endswith(('.smb','.smbh')):
                continue
            totals['blobs'] += 1
            parsed = inspect_asm(blob)
            entities = [r for r in parsed['records']if r['record_kind']=='entity'and r['section']in('geometry','trailing_states')]
            by_ordinal = {i:r for i,r in enumerate(entities)}
            ordinal_by_record = {r['index']:i for i,r in by_ordinal.items()}
            initial = [r for r in entities if r['section']=='geometry'and r['name']=='ATTRIB_CUSTOM-attrib']
            initial_ids = {r['index']for r in initial}
            row = {'file':relative,'member':member,'blob_sha256':_hash(blob),
                   'complete_token_stream':parsed['complete_token_stream'],
                   'geometry_entity_ordinal_count':len(entities),
                   'custom_attribute_definition_counts_by_section':{}, 'initial_attribute_classification_counts':{},
                   'initial_generic_term_counts':{},'initial_generic_component_counts':{},'unresolved_count':0}
            for rec in entities:
                if 'attrib' in rec['name'].lower():
                    attribute_kinds[rec['section']][rec['name']] += 1
                if rec['name']!='ATTRIB_CUSTOM-attrib':
                    continue
                ts = rec['tokens']
                definition = ts[5]['value']if len(ts)>5 and ts[5]['kind']=='string'else '<unframed-definition>'
                owner = by_ordinal.get(ts[4]['value'])if len(ts)>4 and ts[4]['kind']=='pointer'else None
                owner_kind = owner['name']if owner else '<invalid-or-unresolved-owner>'
                section_definitions[rec['section']][definition] += 1
                section_owner_kinds[(rec['section'],definition)][owner_kind] += 1
                row['custom_attribute_definition_counts_by_section'].setdefault(rec['section'],Counter())[definition] += 1
            if not parsed['complete_token_stream']:
                failures.append({'file':relative,'member':member,'stage':'ASM_tokenization',
                                 'reason':parsed.get('unresolved_reason'), 'initial_custom_attributes_observed':len(initial)})
                blobs.append(row)
                continue
            try:
                decoded = decode_asm_generic_tags(blob,parsed=parsed,allow_fpm_tracking=True)
            except Exception as error:
                failures.append({'file':relative,'member':member,'stage':'shared_initial_attribute_reader','reason':str(error)})
                blobs.append(row)
                continue
            classified = {}
            for key,status in (('tags','OwnedGenericName'),('ignored_validated_other_definition_attributes','ValidatedOtherDefinition'),('unresolved','Unresolved')):
                for item in decoded[key]:
                    identity = item['attribute_record_index']
                    if identity in classified or identity not in initial_ids:
                        inventory_errors.append({'file':relative,'member':member,'attribute_record_index':identity,
                                                 'reason':'Shared initial attribute classification is duplicated or outside the initial custom inventory'})
                    classified[identity] = (status,item)
            missing = initial_ids-set(classified)
            if missing:
                inventory_errors.append({'file':relative,'member':member,'unclassified_initial_attribute_record_indices':sorted(missing)})
            local_terms,local_components,local_status = Counter(),Counter(),Counter()
            for rec in initial:
                ts = rec['tokens']
                definition = ts[5]['value']if len(ts)>5 and ts[5]['kind']=='string'else '<unframed-definition>'
                owner = by_ordinal.get(ts[4]['value'])if len(ts)>4 and ts[4]['kind']=='pointer'else None
                owner_kind = owner['name']if owner else '<invalid-or-unresolved-owner>'
                status,item = classified.get(rec['index'],('Unclassified',{}))
                local_status[status] += 1
                definition_status[definition][status] += 1
                proof = {'file':relative,'member':member,'attribute_record_index':rec['index'],
                         'attribute_geometry_entity_ordinal':ordinal_by_record[rec['index']],
                         'attribute_byte_offset':rec['offset'],'definition_name':definition,'owner_kind':owner_kind,
                         'stored_owner_geometry_entity_ordinal':ts[4]['value']if len(ts)>4 else None,
                         'owner_inspection_record_index':owner['index']if owner else None}
                term_count,component_counts = None,()
                if definition=='generic_tag_attrib_def':
                    try:
                        raw_count, raw_cs, empty = _raw_counted_extent(rec)
                        raw_terms[raw_count] += 1; raw_components.update(raw_cs)
                        totals['raw_empty_name_terms'] += empty
                    except (ValueError,KeyError,IndexError,UnicodeError) as error:
                        failures.append(dict(proof,stage='raw_counted_extent_observation',reason=str(error)))
                    try:
                        nested_metadata = (status=='ValidatedOtherDefinition'
                            and item.get('owner_kind')=='ATTRIB_CUSTOM-attrib'
                            and item.get('parent_topology_owner_kind') in ('body','face')
                            and isinstance(item.get('parent_topology_owner_record_index'),int)
                            and item.get('owner_attribute_chain')==[rec['index']]
                            and bool(item.get('parent_owner_attribute_chain')))
                        payload = decode_counted_asm_name(rec,allow_empty_names=nested_metadata)
                        if nested_metadata and any(item.get(key)!=value for key,value in payload.items()):
                            raise ValueError('Shared qualified nested metadata differs from its exact counted payload')
                        encoded = encode_generic_tag_payload(payload)
                        if encoded!=blob[payload['payload_offset']:payload['payload_end_offset']]:
                            raise ValueError('Counted generic name exact source payload replay disagrees')
                        term_count = payload['stored_term_count']
                        component_counts = tuple(t['stored_reference_component_count']for t in payload['terms'])
                        if nested_metadata:
                            nested_terms[term_count] += 1
                            nested_components.update(component_counts)
                            totals['nested_metadata_payload_byte_replays'] += 1
                        else:
                            payload_terms[term_count] += 1
                            payload_components.update(component_counts)
                            totals['generic_name_payload_byte_replays'] += 1
                        local_terms[term_count] += 1
                        local_components.update(component_counts)
                        if status=='OwnedGenericName':
                            owned_terms[term_count] += 1
                            owned_components.update(component_counts)
                    except (ValueError,KeyError,IndexError,UnicodeError,struct.error) as error:
                        failures.append(dict(proof,stage='pure_counted_name_payload',reason=str(error)))
                group_key = (definition,owner_kind,status,term_count,component_counts)
                if group_key not in framing_groups:
                    framing_groups[group_key] = {'count':0,'example':proof}
                framing_groups[group_key]['count'] += 1
                if status=='Unresolved':
                    diagnostic = dict(proof,reason=item['reason'])
                    diagnostics.append(diagnostic)
                    frontier_groups[(definition,owner_kind,item['reason'])].append(diagnostic)
            totals.update(local_status)
            row['initial_attribute_classification_counts'] = _counts(local_status)
            row['initial_generic_term_counts'] = _counts(local_terms)
            row['initial_generic_term_count_scope'] = 'All framed generic payloads in this blob, including separately qualified nested metadata; global summary separates ordinary/nested scopes.'
            row['initial_generic_component_counts'] = _counts(local_components)
            row['unresolved_count'] = len(decoded['unresolved'])
            blobs.append(row)
    source_after = {name:_hash((root/name).read_bytes())for name in SOURCES}
    if source_after!=source_hashes:
        raise ValueError('An audited reader source changed during the corpus run; rerun after coordinated edits stop')
    actual_discovery = {'archive_count':len(files),'blob_count':totals['blobs'],
        'initial_custom_definition_counts':_counts(section_definitions['geometry']),
        'initial_generic_term_counts':_counts(raw_terms),'initial_generic_component_counts':_counts(raw_components)}
    comparisons = {key:{'matches_prior_discovery':actual_discovery[key]==DISCOVERY[key],
                        'prior':DISCOVERY[key],'current':actual_discovery[key]}for key in actual_discovery}
    canonical_manifest = json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
    return {'scope':'Saved-corpus initial ASM custom attribute payload/owner-chain framing and exact counted generic naming audit. Raw trailing attribute counts are inventories only; no complete-format coverage percentage.',
        'provenance':{'repository_HEAD_at_start':revision,'reader_source_sha256':source_hashes,
                      'reader_sources_unchanged_during_run':True,'archive_discovery':'Sorted root.glob("*/*.f3d") in the saved capture layout; no temporary discovery file is read.',
                      'archive_manifest_sha256':_hash(canonical_manifest),'archive_manifest':manifest,
                      'prior_discovery':DISCOVERY,'prior_discovery_comparison':comparisons},
        'archive_count':len(files),'blob_count':totals['blobs'],
        'initial_custom_attribute_count':sum(section_definitions['geometry'].values()),
        'initial_attribute_classification_counts':_counts(Counter({k:v for k,v in totals.items()if k in ('OwnedGenericName','ValidatedOtherDefinition','Unresolved','Unclassified')})),
        'custom_definition_counts_by_section':{s:_counts(c)for s,c in sorted(section_definitions.items())},
        'custom_definition_owner_kind_inventory':[{'section':s,'definition_name':d,'owner_kind_counts':_counts(c)}for (s,d),c in sorted(section_owner_kinds.items())],
        'attribute_entity_record_kind_counts_by_section':{s:_counts(c)for s,c in sorted(attribute_kinds.items())},
        'initial_definition_framing_status_counts':{d:_counts(c)for d,c in sorted(definition_status.items())},
        'raw_initial_generic_counted_extents':{'term_count_distribution':_counts(raw_terms),'component_count_distribution_per_term':_counts(raw_components),
            'empty_name_term_occurrences':totals['raw_empty_name_terms'],
            'scope':'Literal counted length/component/terminator observations only; includes empty names rejected by the production payload parser, and does not qualify owners or semantic identity.'},
        'initial_generic_payload_framing':{'term_count_distribution':_counts(payload_terms),'component_count_distribution_per_term':_counts(payload_components),
                                          'exact_source_payload_replays':totals['generic_name_payload_byte_replays'],
                                          'scope':'Ordinary strict nonempty topology naming payloads only; separately qualified nested metadata is excluded from these counts.'},
        'nested_metadata_payload_framing':{'term_count_distribution':_counts(nested_terms),
            'component_count_distribution_per_term':_counts(nested_components),
            'exact_source_payload_replays':totals['nested_metadata_payload_byte_replays'],
            'scope':'Empty-name opt-in only for shared-reader-qualified singleton metadata whose immediate owner is an attribute and whose BODY/FACE root owner and parent chain are explicit. These records are not topology naming candidates.'},
        'owned_initial_generic_names':{'term_count_distribution':_counts(owned_terms),'component_count_distribution_per_term':_counts(owned_components)},
        'counted_owner_framing_inventory':[{'definition_name':d,'owner_kind':o,'classification':s,'term_count':t,
                                          'component_counts_in_stored_order':list(cs),**row}
                                         for (d,o,s,t,cs),row in sorted(framing_groups.items(),key=lambda item:str(item[0]))],
        'unresolved_diagnostic_count':len(diagnostics),
        'frontier_summary':[{'definition_name':d,'owner_kind':o,'reason':r,'count':len(rows),'representative':rows[0]}
                            for (d,o,r),rows in sorted(frontier_groups.items(),key=lambda item:(-len(item[1]),item[0]))],
        'blobs_with_initial_attribute_diagnostics':sum(bool(b['unresolved_count'])for b in blobs),
        'read_or_framing_failure_count':len(failures),
        'failure_stage_counts':_counts(Counter(f['stage']for f in failures)),
        'namespace_scope':'Owner pointers are resolved through initial-plus-trailing geometry-entity ordinals, excluding section markers/history records. Attribute and owner inspection indices are separately retained; equality in initial geometry does not merge the namespaces.',
        'unresolved_groups':[{'definition_name':d,'owner_kind':o,'reason':r,'count':len(rows),'entries':rows}
                             for (d,o,r),rows in sorted(frontier_groups.items(),key=lambda item:(-len(item[1]),item[0]))],
        'inventory_classification_errors':inventory_errors,'read_or_framing_failures':failures,
        'blobs':blobs,'elapsed_seconds':round(time.monotonic()-started,3),
        'limits':['A validated generic naming payload/owner chain is not a persistent topology ID or qualified selected source.',
                  'FPM/FDM literals and opaque fields retain their existing reader scope; raw trailing attributes are not relabeled validated initial attributes.',
                  'Zero framing diagnostics in these saved captures do not establish complete procedural geometry, lifecycle, all custom definitions, native writing or regeneration.',
                  'Term/component counts describe observed serialized occurrences, including repeated blobs/caches; they are not independent feature experiments.',
                  'No live Fusion, API capture or full main-reader corpus decode is run.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--zstd-library',type=Path)
    p.add_argument('--report',type=Path)
    args=p.parse_args()
    zstd=args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result=audit(args.root,zstd)
    (args.report or args.root/'asm-attribute-frontier-current.json').write_text(json.dumps(result,indent=2)+'\n')
    summary={k:result[k]for k in ('archive_count','blob_count','initial_custom_attribute_count',
        'initial_attribute_classification_counts','unresolved_diagnostic_count','blobs_with_initial_attribute_diagnostics',
        'read_or_framing_failure_count','failure_stage_counts','elapsed_seconds')}
    summary['inventory_classification_error_count']=len(result['inventory_classification_errors'])
    summary['frontier_groups']=[{k:g[k]for k in ('definition_name','owner_kind','reason','count')}for g in result['frontier_summary']]
    print(json.dumps(summary,indent=2))
