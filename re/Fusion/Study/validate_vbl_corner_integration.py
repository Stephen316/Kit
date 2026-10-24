"""Four saved outputs: only report-qualified VBL corner summaries may change.

Cache arguments avoid repeated main decoding. Without caches, the explicit CLI
run computes this fixed manifest once at the pinned baseline and current code.
No live Fusion/API/UI access occurs.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from validate_history_cache_integration import differences

ROOT=Path(__file__).resolve().parent
BASELINE='a87431e'
EVIDENCE='vbl-boundary-corner-decoding.json'
FILES=('specialfillets-d50f7a4f04e0/rule_asymmetric.f3d',
       'specialfillets-d50f7a4f04e0/rule_all_both.f3d',
       'edgemodes-87edbf67527b/fillet_chord.f3d',
       'patchcontinuity-b9b0be85a281/brep_tangent.f3d')
WARNING='VBL component definitions decoded; standalone XYZ surface evaluator remains unsupported'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def evidence():
    report=json.loads((ROOT/EVIDENCE).read_text());proof={}
    for sample in report['samples']+report['old_controls']:
        filename=sample.get('archive',sample.get('file'))
        if filename not in FILES:continue
        key=(filename,sample['member'])
        if key in proof:raise AssertionError(('Duplicate VBL corner golden',key))
        proof[key]=sample['expected_summary']
    if {key[0] for key in proof}!=set(FILES):raise AssertionError('Every fixed archive requires independent positive/empty ASM evidence')
    return proof


def compare(before,current,filename,proof):
    after=copy.deepcopy(current);matched=set();published=faces=corners=warnings=0
    old_streams=before['asm_decoding']['streams'];streams=after['asm_decoding']['streams']
    assert len(old_streams)==len(streams),(filename,'ASM stream count changed')
    for old,new in zip(old_streams,streams):
        assert old['member']==new['member'],(filename,'ASM member/order changed')
        key=(filename,new['member']);old_topology=old['topology'];topology=new['topology']
        assert topology.get('unresolved')==old_topology.get('unresolved'),(filename,key,'VBL interior or other warnings changed')
        assert topology.get('vbl_component_boundaries')==old_topology.get('vbl_component_boundaries'),(filename,key,'Existing component proof changed')
        if 'vbl_boundary_corners' not in topology:
            assert key not in proof or not(proof[key]['decoded'] or proof[key]['unresolved']),(filename,key,'Positive golden missing')
            continue
        assert 'vbl_boundary_corners' not in old_topology,(filename,key,'Unexpected prior corner summary')
        summary=topology.pop('vbl_boundary_corners')
        assert key in proof and summary==proof[key],(filename,key,'Full independent corner golden differs')
        assert summary['decoded'] and not summary['unresolved'],(filename,key,'Only actual eight-corner-face positive publication observed')
        partial=[x for x in topology['unresolved'] if x.get('reason')==WARNING]
        assert len(partial)==len(summary['decoded'])==8,(filename,key,'Eight interior warnings must remain explicit')
        for row in summary['decoded']:
            assert row['surface_record_index'] in {x['index'] for x in partial}
            assert row['VBL_interior_geometry'] is row['component_parameter_orientation'] is row['native_edge_parameter_mapping'] is None
            cycle=row['ordered_vertex_cycle']
            assert len(row['boundary_edges'])==len(row['corners'])==6 and len(cycle)==7 and cycle[0]==cycle[-1] and len(set(cycle[:-1]))==6
        matched.add(key);published+=1;faces+=len(summary['decoded']);corners+=sum(len(row['corners']) for row in summary['decoded']);warnings+=len(partial)
    expected={key for key,summary in proof.items() if key[0]==filename and (summary['decoded'] or summary['unresolved'])}
    assert matched==expected,(filename,'Missing or extra published VBL corner blob',matched^expected)
    assert after==before,(filename,'Unqualified output changes',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),published_boundary_summaries=published,qualified_VBL_faces=faces,qualified_boundary_corners=corners,retained_VBL_interior_warnings=warnings,
        whole_output_exact_after_removing_only_qualified_corner_summary=True,old_component_proofs_geometry_placement_and_warnings_exact=True,
        whole_output_unchanged=before==current,baseline_output_sha256=digest(before),current_output_sha256=digest(current),qualified_difference_paths=differences(before,current))


def read_cache(path,side):
    value=json.loads(Path(path).read_text())
    if isinstance(value,list):return value
    if 'files' in value:assert value['files']==list(FILES),'Cache manifest differs'
    if 'baseline_commit' in value:assert str(value['baseline_commit']).startswith(BASELINE),'Cache baseline differs'
    return value[side]


def validate(zstd,baseline_cache=None,current_cache=None):
    if baseline_cache:
        before=read_cache(baseline_cache,'before')
    else:
        from validate_history_cache_integration import baseline_outputs
        before=baseline_outputs(FILES,zstd,revision=BASELINE)
    if current_cache:
        current=read_cache(current_cache,'after')
    else:
        from decode_basics import decode_basics
        current=json.loads(json.dumps([decode_basics(ROOT/name,zstd) for name in FILES]))
    assert len(before)==len(current)==len(FILES)==4
    assert [x['file'] for x in before]==[str(ROOT/name) for name in FILES]==[x['file'] for x in current]
    proof=evidence();rows=[compare(a,b,name,proof) for a,b,name in zip(before,current,FILES)]
    summary={key:sum(row[key] for row in rows) for key in ('published_boundary_summaries','qualified_VBL_faces','qualified_boundary_corners','retained_VBL_interior_warnings')}
    assert summary==dict(published_boundary_summaries=1,qualified_VBL_faces=8,qualified_boundary_corners=48,retained_VBL_interior_warnings=8)
    assert sum(row['whole_output_unchanged'] for row in rows)==3
    summary.update(saved_files=4,whole_output_unchanged_controls=3,unexpected_changes=0,live_API_calls=0,baseline_main_calls=0 if baseline_cache else 4,current_main_calls=0 if current_cache else 4)
    caches={}
    if baseline_cache:caches['baseline']=dict(path=str(Path(baseline_cache).resolve()),sha256=sha(baseline_cache))
    if current_cache:caches['current']=dict(path=str(Path(current_cache).resolve()),sha256=sha(current_cache))
    sources=('validate_vbl_corner_integration.py','decode_vbl_boundary_corners.py','decode_vbl_components.py','asm_records.py','decode_brep.py','decode_basics.py')
    return dict(scope='Fixed four-file integration against a87431e; only exact independently qualified topology.vbl_boundary_corners publication admitted',baseline_commit=BASELINE,files=list(FILES),summary=summary,samples=rows,
        evidence_sha256={EVIDENCE:sha(ROOT/EVIDENCE)},cache_provenance=caches,source_sha256={p:sha(ROOT/p) for p in sources},
        limitations=['Eight VBL interior warnings remain; topological boundary traversal is not UV orientation or native edge parameter correspondence',
            'All existing geometry, component dictionaries, selection evidence, placement labels and unqualified diagnostics remain exact',
            'No live Fusion calls, API capture, procedural surface fitting, native writer or regeneration',
            'Cache paths are optional execution conveniences; omitting them reproduces the fixed baseline/current comparison from local Git and saved archives'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache');p.add_argument('--current-cache');p.add_argument('--zstd-library');p.add_argument('--output',default='vbl-corner-integration.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z,a.baseline_cache,a.current_cache);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
