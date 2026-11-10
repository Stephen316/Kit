"""FixedSpline Sweep native source, captured API numerics and separate result facts."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_asm_subtypes import decode_asm_subtypes
from decode_assembly import decode_assembly
from decode_basics import decode_sketches
from decode_body_properties import decode_body_properties
from decode_body_bindings import decode_body_bindings
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_brep import decode_topology
from decode_nurbs import numeric_array
from decode_placement import decode_placement
from decode_sketch import reference
from decode_sweep_fixed_spline_paths import decode_sweep_fixed_spline_paths
from decode_sweep_fixed_spline_sources import resolve_sweep_fixed_spline_path,SCOPE
from validate_mesh_remesh import load

CAPTURE='sweepnurbspaths-7ded30a4b9ae'


def load_sources(root,archive,zstd):
    args=load(root,archive,zstd);decode_sketches(args[0],args[1],args[2]);decode_placement(args[0],args[1],args[2]);return args


def near(a,b,tolerance=1e-11):
    if isinstance(a,(list,tuple)) and isinstance(b,(list,tuple)):return len(a)==len(b) and all(near(x,y,tolerance) for x,y in zip(a,b))
    return abs(a-b)<=tolerance


def validate(root,zstd):
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text());journal=[json.loads(x) for x in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks,samples,guards=[],[],[]
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    check('Actual three healthy exported Sweep captures complete',(root/CAPTURE/'complete.txt').is_file() and len(truth['samples'])==3 and not truth['errors'] and journal[-1]['terminal_status']=='Complete')
    closes=[j for j in journal if j['phase']=='owned_document_close_returned']
    check('All owned3 closeFalse returnedTrue',len(closes)==3 and all(j['returned'] is True and j['save'] is False for j in closes))
    check('Exact executed generator source snapshot',hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file'];data,records,features,member,members=load_sources(root,archive,zstd);before=copy.deepcopy(features)
        early=decode_sweep_fixed_spline_paths(data,records,features)
        check(archive+' shared controls and source callback succeed',len(early['decoded'])==1 and not early['unresolved'])
        row=early['decoded'][0];path=row['settings']['path'];source=path['native_source_evidence'];shape=source['source_nurbs'];fid=row['feature_object_id']
        source_row=dict(feature_object_id=fid,native_source_evidence=source,scope=SCOPE)
        check(archive+' actual archive hash',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        check(archive+' explicit proxy descriptor leaf and source tag retained',path['count']==1 and path['segments'][0]['curve_object_id']==source['selection']['curve_object_id'] and path['segments'][0]['descriptor_object_id']==source['selection']['descriptor_object_id'] and path['selection_record_object_id']==source['selection']['selection_record_object_id'])
        constructor=actual['constructor_inout_arrays'];api_source=actual['source_spline_before_sweep']
        check(archive+' native controls match actual constructor inout arrays',shape['control_points_cm']==constructor['control_points_cm'] and shape['knots']==constructor['knots'] and shape['weights']==(constructor['weights'] or []))
        check(archive+' source kind corroborated by actual SDK object type',api_source['objectType']=='adsk::fusion::SketchFixedSpline')
        for frame in ('geometry_local','geometry_world'):
            api=api_source[frame];fields=api['getData_fields']
            check(archive+' '+frame+' actual getData degree knots weights flags',fields['return_value'] is True and fields['degree']==shape['degree'] and fields['knots']==shape['knots'] and fields['weights']==shape['weights'] and fields['isRational']==shape['is_rational'] and fields['isPeriodic']==shape['is_periodic'])
            check(archive+' '+frame+' controlpointVector metadata explicitly notnumericAPIarray',isinstance(fields['controlPoints'],dict) and fields['controlPoints']['python_type']=='Point3DVector' and api['controlPointCount']==len(shape['control_points_cm']))
            check(archive+' '+frame+' evaluator domain',api['evaluator_parameter_extents'][0] is True and near(api['evaluator_parameter_extents'][1:],shape['parameter_domain']))
            pointkey='point_sketch_local_cm' if frame=='geometry_local' else 'point_component_cm'
            derivativekey='natural_parameter_derivative_sketch_local' if frame=='geometry_local' else 'natural_parameter_derivative_component'
            derived=source['natural_derived_samples'];endpoints=[derived[0][pointkey],derived[-1][pointkey]]
            check(archive+' '+frame+' actual evaluator endpoints numerical corroboration',api['evaluator_endpoints'][0] is True and near(endpoints,api['evaluator_endpoints'][1:]))
            check(archive+' '+frame+' actual start derivative numerical corroboration',api['evaluator_start_first_derivative'][0] is True and near(derived[0][derivativekey],api['evaluator_start_first_derivative'][1]))
        check(archive+' canonical native identity frame agrees actual recorded transform',source['canonical_placement']['sketch_to_component_matrix']==api_source['parentSketch']['transform'] and source['source_component_object_id']==3)
        actual_paths=[actual['exact_path_argument_before_sweep'],actual['feature_before_node']['path']]
        check(archive+' actual opposition false retained separately from unknownnativeflag',all(p['count']==1 and p['isClosed'] is False and p['entities'][0]['isOpposedToEntity'] is False for p in actual_paths) and path['segments'][0]['path_is_opposed_to_entity'] is None and source['path_is_opposed_to_entity'] is None)
        check(archive+' five interior/natural samples markedderived notAPIverification',len(source['natural_derived_samples'])==5 and 'no API interior-sample verification' in source['evaluator_scope'])
        # Independent existing BODY readers prove output ownership/ASM IDs; no new runtime route parser.
        props=decode_body_properties(data,records,decode_assembly(data,records,[]))
        anchors=row['settings']['result_body_anchors'];check(archive+' one explicit independently owned result anchor',len(anchors)==1 and anchors[0]['source_owner_object_id']==fid)
        native_body=anchors[0]['native_body_object_id'];owned=[p for p in props['bodies'] if p['object_id']==native_body]
        check(archive+' reciprocal currentBODY owner agrees source component',len(owned)==1 and owned[0]['component_object_id']==source['source_component_object_id'])
        mappings=decode_body_bindings(data,records,member,dict(streams=[dict(member=n) for n in members if n.endswith('.smbh')]),props)
        chosen=[m for m in mappings['decoded'] if [b['native_body_object_id'] for b in m['bindings']]==[native_body]]
        check(archive+' canonical exact sameasset nativeBODY mapping',len(chosen)==1)
        identifiers=decode_body_asm_identifiers(data,records,member,members,dict(decoded=chosen))
        check(archive+' initial ASM storedBODY IDs separately qualified',len(identifiers['decoded'])==1 and not identifiers['unresolved'])
        mapping=identifiers['decoded'][0];raw=members[mapping['history_blob_member']];parsed=inspect_asm(raw);catalog=decode_asm_subtypes(raw,parsed=parsed);topology=decode_topology(parsed,subtype_catalog=catalog)
        graph=next(g for g in topology['body_graphs'] if g['body_index']==mapping['bindings'][0]['asm_body_index'])
        api_bodies=actual['component_bodies_after_sweep']
        check(archive+' before-node and current result membership observations separate',len(actual['feature_before_node']['bodies'])==0 and len(actual['feature_at_timeline_end']['bodies'])==1 and len(api_bodies)==1)
        native_bundle=dict(vertex_count=graph['counts']['vertex'],edge_count=graph['counts']['edge'],face_count=graph['counts']['face'],unordered_vertices_cm=sorted([round(x,12) for x in p] for p in graph['raw_vertex_positions']))
        api_bundles=[dict(vertex_count=len(b['vertices']),edge_count=b['edge_count'],face_count=b['face_count'],unordered_vertices_cm=sorted([round(x,12) for x in p['position_cm']] for p in b['vertices'])) for b in api_bodies]
        check(archive+' resultvertex/count data corroborates singletonAPIcollection',graph['body_transform_is_identity'] is True and len(api_bundles)==1 and native_bundle==api_bundles[0])
        check(archive+' actual catalogue-aware result topology diagnostics retained',parsed['complete_token_stream'] is True and not topology['unresolved'])
        check(archive+' source/feature dictionaries unmutated by readers',features==before)
        result_proof=dict(owned_body_anchor=anchors[0],body_properties=owned[0],native_history_mapping=chosen[0],stored_asm_body_identifiers=identifiers,
            ASM_topology_unresolved=topology['unresolved'],ASM_body_counts=graph['counts'],native_vertex_count_bundle=native_bundle,actual_API_vertex_count_bundles=api_bundles,
            native_API_body_assignment=None,scope='Independent existing native BODY/ASM identifier readers only. Vertex/count data corroborates the singleton API collection; no surface evaluator, volume reconstruction, source/result or temporary-ID assignment. Existing production ASM diagnostics are untouched.')
        samples.append(dict(archive=archive,feature_object_id=fid,expected_path=path,expected_source_row=source_row,
            expected_source_summary=dict(decoded=[source_row],unresolved=[],scope=SCOPE),
            actual_constructor_inout_arrays=constructor,actual_API_controlPointVector_metadata=api_source['geometry_local']['getData_fields']['controlPoints'],
            actual_API_path_opposition_flags=[p['entities'][0]['isOpposedToEntity'] for p in actual_paths],
            actual_API_before_node_feature_body_count=len(actual['feature_before_node']['bodies']),
            actual_API_timeline_end_feature_body_count=len(actual['feature_at_timeline_end']['bodies']),
            actual_API_current_component_body_count=len(api_bodies),
            independent_result_body_ASM_evidence=result_proof))
        if shape['is_rational']:saved=(data,records,features,path,source,fid)
    data,records,features,path,source,fid=saved;path_id=path['selection_record_object_id']
    def guard(label,mutation=None,change_features=None):
        bad=bytearray(data);own_features=copy.deepcopy(features)
        if mutation:mutation(bad)
        if change_features:change_features(own_features)
        try:resolve_sweep_fixed_spline_path(bytes(bad),records,path_id,fid,own_features)
        except (ValueError,KeyError,IndexError,struct.error,UnicodeError,ArithmeticError) as error:reason=str(error)
        else:raise AssertionError(label)
        checks.append(label);guards.append(dict(guard=label,reason=reason))
    descriptor=next(r for r in records if r.is_primary and r.object_id==source['selection']['descriptor_object_id'])
    guard('Reject owned descriptor/feature mismatch',lambda b:struct.pack_into('<Q',b,descriptor.body+253,fid+1))
    leaf=next(r for r in records if r.is_primary and r.object_id==source['selection']['terminal_object_id'])
    guard('Reject explicit leaf curve-tag mismatch',lambda b:struct.pack_into('<Q',b,leaf.body+18,99999))
    geometry=next(r for r in records if r.start==source['native_geometry_continuation_record_offset'])
    guard('Reject stored spline owner disagreement',lambda b:struct.pack_into('<Q',b,geometry.end-10,99999))
    def tamper_shape(fs):
        sketch=next(f for f in fs if f['kind']=='Sketch' and f['sketch_object_id']==source['selection']['sketch_object_id'])
        curve=next(g for g in sketch['geometry'] if g['object_id']==source['selection']['curve_object_id']);curve['nurbs']['control_points_cm'][1][0]+=.1
    guard('Reject canonical source shape disagreeing with native continuation',change_features=tamper_shape)
    payload=data[geometry.body:geometry.end];_,weights_cursor=numeric_array(payload,75)
    guard('Reject nonpositive native rational weight',lambda b:struct.pack_into('<d',b,geometry.body+weights_cursor+12,0.))
    def tamper_frame(fs):
        sketch=next(f for f in fs if f['kind']=='Sketch' and f['sketch_object_id']==source['selection']['sketch_object_id']);sketch['placement']['sketch_to_component_matrix'][0]=2.
    guard('Reject unproved nonrigid canonical placement',change_features=tamper_frame)
    guard('Reject stored periodic flag outside captured sourcefamily',lambda b:b.__setitem__(geometry.body+62,1))
    sources=('decode_sweep_fixed_spline_sources.py','validate_sweep_fixed_spline_sources.py','decode_sweep_fixed_spline_paths.py','decode_sweep_modes.py','decode_nurbs.py','decode_selection.py','decode_placement.py','decode_loft_composite_guides.py')
    return dict(sample_count=3,native_fixed_spline_source_count=3,independent_result_BODY_count=3,API_endpoint_comparison_count=12,API_start_derivative_comparison_count=6,
        check_count=len(checks),malformed_guard_count=len(guards),samples=samples,checks=checks,malformed_guards=guards,
        actual_document_close_journal=closes,actual_terminal_journal=journal[-1],
        capture_provenance=dict(capture_directory=CAPTURE,executed_generator_sha256=truth['executed_generator_sha256'],sdk_sources=truth['sdk_sources']),
        source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sources},
        limitations=['Native source namespace follows explicit proxy/descriptor/sketchID/tag; numerical geometry does not choose identity',
            'API controlPointVector serializes metadata only; numeric controls corroborated by actual constructorinout arrays, not claimed directAPIcontrolpoint getter proof',
            'API knots/weights/degree/flags, endpoints and startderivatives independently corroborate the native source',
            'Interior samples are derived; no actual API interior evaluator samples captured',
            'All actual API oppositionflags false; native opposition remainsNone and natural knot-domain order is not a traversal flag',
            'Captured sourceframe is typed implicitIdentity parentcomponent; no nonidentity or assemblyworld claim',
            'Independent canonical outputBODY mappings and vertexcounts do not decode Sweep surfaces/solver/regeneration',
            'Existing production resultASM diagnostics remain unchanged; catalogue-aware focused diagnostics separately retained'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='sweep-fixed-spline-source-decoding.json');args=parser.parse_args()
    root=Path(__file__).resolve().parent;z=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(root,z);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('sample_count','check_count','malformed_guard_count')}))

if __name__=='__main__':main()
