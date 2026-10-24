"""Saved reverse-only native naming registries and strict old-schema controls."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from decode_native_naming_registry import decode_native_naming_registry,encode_native_naming_registry,REGISTRY
from fusion_archive import read_members
from fusion_metadata import design_records

BASELINE='1bdc9bc'


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate(root,zstd):
    source=subprocess.run(['git','show',BASELINE+':decode_native_naming_registry.py'],cwd=root,check=True,text=True,capture_output=True).stdout
    old_module={'__name__':'native_naming_registry_baseline'}
    exec(compile(source,BASELINE+'-decode_native_naming_registry.py','exec'),old_module)
    old_decode=old_module['decode_native_naming_registry']
    frozen_census_bytes=subprocess.run(['git','show',BASELINE+':native-naming-registry-frontier.json'],cwd=root,check=True,capture_output=True).stdout
    frozen_census=json.loads(frozen_census_bytes)
    frozen_files={row['file']:row for row in frozen_census['file_manifest']}
    checks,previous,variants,guards=0,[],[],[]
    totals,shapes,classes=Counter(),Counter(),Counter()
    reverse_example=paired_example=None
    files=sorted(root.glob('*/*.f3d'))

    def check(test,reason):
        nonlocal checks
        if not test:
            raise AssertionError(reason)
        checks+=1

    for path in files:
        relative=str(path.relative_to(root))
        frozen=relative in frozen_files
        if frozen:
            check(hashlib.sha256(path.read_bytes()).hexdigest()==frozen_files[relative]['sha256'],
                  'actual frozen capture bytes remain identical to original census manifest')
        members=read_members(path,zstd)
        for member,data in sorted(members.items()):
            if not member.endswith('/FusionDesignSegmentType1/BulkStream.dat'):
                continue
            records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
            primary_groups={}
            for rec in records:
                if rec.is_primary:
                    primary_groups.setdefault(rec.object_id,[]).append(rec)
            primary={i:rs[0]for i,rs in primary_groups.items()if len(rs)==1}
            before=old_decode(data,records);after=decode_native_naming_registry(data,records)
            current={r['object_id']:r for r in after['decoded']}
            old={r['object_id']:r for r in before['decoded']}
            check(not after['unresolved'],'every observed registry layout has strict admitted framing')
            targets=[r for r in records if r.is_primary and r.class_guid==REGISTRY]
            check(len(current)==len(targets),'every actual typed primary registry is classified once')
            for identity,row in old.items():
                check(current[identity]==row,'previously admitted registry dictionary is exactly unchanged')
                previous.append({'file':str(path.relative_to(root)),'member':member,'object_id':identity,
                    'canonical_dictionary_sha256':_digest(row),'exact_unchanged':True,'in_frozen_census_manifest':frozen})
                totals['previous_registry_dictionaries_exact']+=1
                totals['frozen_previous_registry_dictionaries_exact'if frozen else'additional_current_old_schema_controls_exact']+=1
                if row['owner_to_keys']and paired_example is None:
                    paired_example=data,records,row
            rejected={r['object_id']:r for r in before['unresolved']}
            for identity,row in current.items():
                rec=primary[identity];body=data[rec.body:rec.end]
                check(encode_native_naming_registry(row)==body,'actual original payload replays exactly without synthesizing forward rows')
                totals['exact_payload_replays']+=1
                if identity in old:
                    continue
                check(rejected[identity]['reason']=='Native naming reverse count or exact footer extent disagrees',
                      'new layout is exactly the previously observed count/footer rejection')
                check(struct.unpack_from('<I',body,2)[0]==0 and row['owner_to_keys']==[],
                      'stored empty forward owner table is preserved literally')
                n,=struct.unpack_from('<I',body,6)
                check(n==len(row['key_to_owner'])and n>0 and len(body)==25+16*n,
                      'nonempty second table and exact normal footer bound the entire reverse-only payload')
                check(row['table_layout']=='StoredReverseOnly'and row['reciprocity_status']=='ForwardTableAbsent'
                      and row['registry_is_empty']is False,'variant scope explicitly declines absent forward reciprocity')
                pairs=[]
                for i,entry in enumerate(row['key_to_owner']):
                    key,owner=struct.unpack_from('<QQ',body,10+16*i)
                    check((key,owner)==(entry['naming_key'],entry['native_owner_object_id']),
                          'each canonical reverse row equals its actual raw little-endian source fields')
                    check(entry['stored_key_field_offset']==rec.body+10+16*i
                          and entry['stored_owner_field_offset']==rec.body+18+16*i,
                          'raw key/owner source offsets remain distinct and exact')
                    check(owner in primary and primary[owner].class_guid==entry['native_owner_class_guid'],
                          'native owner resolves to its independently typed unique primary record')
                    pairs.append((key,owner));classes[entry['native_owner_class_guid']]+=1
                check(len({key for key,_ in pairs})==n,'actual reverse-only keys are unique')
                footer=body[-15:]
                check(footer[:4]==bytes(4)and footer[4]==1 and footer[-2:]==bytes(2),
                      'reverse-only footer is the exact normal zero marker plus typed reference')
                container=primary[row['registry_container_object_id']]
                check(container.class_guid==row['registry_container_class_guid']and data[container.end-33:container.end-22]
                      ==b'\1'+struct.pack('<Q',identity)+bytes(2),
                      'typed native container backlink returns to this exact registry')
                variants.append({'file':str(path.relative_to(root)),'member':member,'previous_diagnostic':rejected[identity],
                    'expected_registry':row,'source_payload_sha256':hashlib.sha256(body).hexdigest(),
                    'typed_registry_container_record_offset':container.start,
                    'typed_container_payload_byte_count':container.end-container.body,
                    'scope':'Only the actual second table establishes stored key-to-typed-owner associations. No reverse-derived forward table or reciprocal ownership is fabricated.'})
                totals['new_reverse_only_registries']+=1;totals['new_reverse_only_rows']+=n;shapes[n]+=1
                totals['frozen_reverse_only_registries' if frozen else 'later_reverse_only_registries']+=1
                totals['frozen_reverse_only_rows' if frozen else 'later_reverse_only_rows']+=n
                if reverse_example is None:
                    reverse_example=data,records,row
    check(totals['frozen_previous_registry_dictionaries_exact']==499 and totals['frozen_reverse_only_registries']==97,
          'observed registry counts: '+str(dict(totals))+'; saved archives: '+str(len(files)))
    check(totals['frozen_reverse_only_rows']==179,'all 179 original reverse-only owner rows remain explicit')

    def rejects(label,example,offset,value,fmt='<Q'):
        data,records,row=example
        changed=bytearray(data);struct.pack_into(fmt,changed,offset,value)
        decoded=decode_native_naming_registry(bytes(changed),records)
        errors=[r for r in decoded['unresolved']if r['object_id']==row['object_id']]
        check(errors and row['object_id']not in {r['object_id']for r in decoded['decoded']},label)
        guards.append({'guard':label,'object_id':row['object_id'],'reason':errors[0]['reason']})
    data,records,row=reverse_example
    first,second=row['key_to_owner'][:2]
    rejects('Reverse-only duplicate key is not accepted',reverse_example,first['stored_key_field_offset'],second['naming_key'])
    rejects('Reverse-only owner must resolve to an actual unique primary record',reverse_example,first['stored_owner_field_offset'],0x7fffffffffffffff)
    rejects('Reverse-only positive key domain remains strict',reverse_example,first['stored_key_field_offset'],0)
    rejects('Counted second table must end at its exact footer',reverse_example,row['stored_reverse_count_offset'],len(row['key_to_owner'])-1,'<I')
    rejects('Reverse-only registry retains exact typed container backlink',reverse_example,row['container_backlink_offset']+1,0)
    data,records,row=paired_example
    reverse=row['key_to_owner'][0]
    rejects('Nonempty forward layout still requires exact reverse reciprocity',paired_example,reverse['stored_owner_field_offset'],row['object_id'])
    return {'stage':'Explicit stored reverse-only native naming registry layout',
        'baseline':{'commit':BASELINE,'module':'decode_native_naming_registry.py','source_sha256':hashlib.sha256(source.encode()).hexdigest(),
                    'frozen_census_report':'native-naming-registry-frontier.json','frozen_census_report_sha256':hashlib.sha256(frozen_census_bytes).hexdigest(),
                    'frozen_census_archive_count':len(frozen_files)},
        'interface':'Existing decode_native_naming_registry(data,records) and encode_native_naming_registry(registry); new layout retains actual empty owner_to_keys and actual populated key_to_owner.',
        'validation':{'checks':checks,'saved_archives':len(files),**dict(totals),'total_registry_records':totals['previous_registry_dictionaries_exact']+totals['new_reverse_only_registries'],
            'reverse_only_second_table_count_distribution':dict(sorted(shapes.items())),
            'reverse_only_typed_native_owner_class_counts':dict(sorted(classes.items())),
            'malformed_guards':guards,'new_API_calls':0,'full_main_decodes':0},
        'findings':['All 97 original variants explicitly store owner_count0 followed by a nonempty counted second table and the unchanged 15-byte typed container footer. Later captured reverse-only registries are counted separately; no partially mismatched nonempty-forward layout is admitted.',
            'Canonical key_to_owner contains the actual stored second-table rows, while owner_to_keys remains actually empty. ForwardTableAbsent is explicit, and no synthetic reverse-derived forward ownership is published.',
            'All 499 previously decoded dictionaries from the frozen 561-archive manifest remain exactly equal, including normal reciprocal and completely empty component registries; newly captured current old-schema controls are counted separately. Existing modifying BoundaryFill logic still requires actual reciprocal owner_to_keys rows.',
            'Every new second-table owner resolves to a unique actual typed primary record; all registry-container references/backlinks and complete original payload bytes validate.',
            'The source keys remain opaque naming literals in the file/asset/registry scope. Counts of occurrences are not globally unique identifiers or independent feature experiments.'],
        'limitations':['Reverse-only association is explicitly one stored direction; no absent forward-table reciprocity, lifecycle, dependency or persistent topology meaning is inferred.',
            'The extension admits only the observed forward_count0/reverse_count>0 branch with unique positive keys, actual typed owners and exact normal footer/backlink. Other count, owner and footer variants remain rejected.',
            'This is a metadata-only check over the saved corpus, with no Fusion API calls, full main pipeline or native file writer.'],
        'previous_registry_controls':previous,'reverse_only_samples':variants}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--zstd-library',type=Path)
    p.add_argument('--report',type=Path)
    args=p.parse_args();z=args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report=validate(args.root,z)
    (args.report or args.root/'naming-registry-variant-decoding.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['validation'],indent=2))
