"""Independent native-profile prism/Scale checks on twelve saved fixtures."""
import argparse
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_scale_reconstruction import decode_scale_reconstruction
from decode_sketch import attributes, numbers, reference
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
FILES = ('tools-fda3948848f4/Scale.f3d','bodymodes-df9b7113539f/scale_uniform.f3d',
    'bodymodes-df9b7113539f/scale_nonuniform.f3d','bodymodes-d696a14d5f0b/scale_holdout.f3d',
    'bodyselections-62e42366c722/scale_two_bodies_point.f3d',
    'scaleshellinputs-97ef1cfd19e4/scale_vertex.f3d',
    'scaleshellinputs-97ef1cfd19e4/scale_construction_point.f3d',
    'scaleshellinputs-97ef1cfd19e4/scale_sketch.f3d',
    'remainingbodyinputs-7b3357274e85/scale_two_sketches.f3d',
    'namedvertexprobe-8d81619f74e6/scale_rational_vertex2.f3d',
    'circularmodes-45f859c1f1b6/body_full.f3d','surfacetools-856ca50cf4c7/offset_positive.f3d')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def sub(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def near(a,b):
    assert len(a)==len(b) and all(math.isfinite(x) for x in list(a)+list(b))
    assert max((abs(x-y) for x,y in zip(a,b)),default=0.)<1e-8,(a,b)


def independent_prism(data,records,members,owner,group):
    """Raw native endpoint IDs and raw ASM pointers, then independent algebra."""
    native_group = next(g for g in owner['native_source_provenance']['source_groups']
        if g['native_body_object_id']==group['source_native_body_object_id'])
    by = {r.object_id:r for r in records if r.is_primary}
    blob = members[group['history_blob_member']]
    parsed = inspect_asm(blob)
    raw = parsed['records']
    def pointer(identity,field,kind):
        token = raw[identity]['tokens'][field]
        target = token['value']
        assert token['tag']==12 and struct.unpack_from('<q',blob,token['offset']+1)[0]==target
        assert target>=0 and raw[target]['section']=='geometry' and raw[target]['name']==kind
        return target
    profile = native_group['profile_cache_correspondence']
    line_edges,point_lines,point_positions = {},{},{}
    for curve in profile['source_curves']:
        record = by[curve['native_entity_object_id']]
        body = data[record.body:record.end]
        props,cursor = attributes(body,2)
        assert props['crv_primary_id']==curve['native_entity_tag'] and props['crv_secondary_id']==0
        endpoint_ids = [reference(body,cursor+107),reference(body,cursor+96)]
        candidates = curve['cached_coedge_candidates']
        edges = {pointer(c['coedge_record_index'],6,'edge') for c in candidates}
        assert len(candidates)==2 and len(edges)==1
        line_edges[record.object_id] = next(iter(edges))
        for point in endpoint_ids:
            point_lines.setdefault(point,[]).append(record.object_id)
            r = by[point]
            payload = data[r.body:r.end]
            _,start = attributes(payload,2)
            point_positions[point] = numbers(payload,start+19,3)
    assert len(line_edges)==len(point_lines)==4 and all(len(v)==2 for v in point_lines.values())
    body_id = group['asm_body_index']
    # Use the explicit serialized BODY route and fixed group EDGE IDs, not point
    # values or the implementation's selected bottom/opposite maps.
    all_edges = [e['edge_index'] for e in group['identity_provenance']['edge_vertex_pairs']]
    all_vertices = {pointer(e,f,'vertex') for e in all_edges for f in (3,5)}
    assert len(all_edges)==12 and len(all_vertices)==8
    bottom,opposite = {},{}
    for point,lines in point_lines.items():
        edges = [line_edges[line] for line in lines]
        candidates = {pointer(edges[0],3,'vertex'),pointer(edges[0],5,'vertex')} & {
            pointer(edges[1],3,'vertex'),pointer(edges[1],5,'vertex')}
        assert len(candidates)==1
        vertex = next(iter(candidates))
        bottom[point] = vertex
        connecting = [edge for edge in all_edges if edge not in set(line_edges.values())
            and vertex in (pointer(edge,3,'vertex'),pointer(edge,5,'vertex'))]
        assert len(connecting)==1
        opposite[point] = next(iter({pointer(connecting[0],3,'vertex'),pointer(connecting[0],5,'vertex')}-{vertex}))
    assert set(bottom.values())|set(opposite.values())==all_vertices
    assert bottom==group['identity_provenance']['bottom'] and opposite==group['identity_provenance']['opposite']
    settings = owner['native_source_provenance']['settings']
    center,factors = settings['reconstruction_center_cm'],settings['factors_xyz']
    placement = native_group['source_sketch']['placement']['sketch_to_component_matrix']
    extent = native_group['extrude_controls']['extent']
    translation = [extent['side_one']['distance_cm']*v for v in native_group['extrude_direction_component']]
    source,scaled = {},{}
    point_rows = []
    for point,position in point_positions.items():
        base = [sum(placement[4*i+j]*position[j] for j in range(3))+placement[4*i+3] for i in range(3)]
        for layer,vertex in ((0,bottom[point]),(1,opposite[point])):
            unscaled = [x+layer*y for x,y in zip(base,translation)]
            transformed = [c+f*(x-c) for x,c,f in zip(unscaled,center,factors)]
            source[vertex],scaled[vertex] = unscaled,transformed
            predicted = next(v for v in group['vertex_correspondence'] if v['vertex_index']==vertex)
            assert predicted['native_sketch_point_object_id']==point and predicted['layer']==layer
            near(predicted['source_position_cm'],unscaled)
            near(predicted['scaled_position_cm'],transformed)
            cached = raw[pointer(vertex,5,'point')]['tokens'][3]['value']
            near(transformed,cached)
            point_rows.append(dict(native_sketch_point_object_id=point,layer=layer,vertex_index=vertex,
                native_derived_source_cm=unscaled,independently_scaled_cm=transformed,stored_cache_cm=cached))
    line_samples = []
    for published in group['native_straight_carrier_correspondence']:
        edge = published['edge_index']
        curve = pointer(edge,8,'straight-curve')
        start,end = pointer(edge,3,'vertex'),pointer(edge,5,'vertex')
        origin,direction = raw[curve]['tokens'][3]['value'],raw[curve]['tokens'][4]['value']
        delta = sub(scaled[end],scaled[start])
        assert math.hypot(*cross(delta,direction))<1e-8
        assert math.hypot(*cross(sub(origin,scaled[start]),delta))<1e-8
        parameters = [raw[edge]['tokens'][i]['value'] for i in (4,6)]
        for fraction in (0.,.5,1.):
            parameter = parameters[0]+fraction*(parameters[1]-parameters[0])
            evaluated = [o+parameter*d for o,d in zip(origin,direction)]
            predicted = [a+fraction*b for a,b in zip(scaled[start],delta)]
            near(evaluated,predicted)
            line_samples.append(dict(edge_index=edge,native_Line_record_index=curve,
                derived_segment_fraction=fraction,native_parameter=parameter,
                independent_native_evaluation=evaluated,independently_scaled_segment_position=predicted))
        for stored,node in ((published['native_cache_edge'] if 'native_cache_edge' in published else published['native_EDGE'],'edge'),
                            (published['native_Line'],'straight-curve')):
            assert stored['kind']==node
        assert published['native_Line']['raw_origin']==origin and published['native_Line']['direction']==direction
    plane_proofs = []
    cap_cycle = None
    for published in group['native_planar_boundary_correspondence']:
        face = published['face_index']
        loop = pointer(face,4,'loop')
        cycle,vertices = [],[]
        current = pointer(loop,4,'coedge')
        while current not in cycle:
            assert len(cycle)<4
            edge = pointer(current,6,'edge')
            endpoints = [pointer(edge,3,'vertex'),pointer(edge,5,'vertex')]
            if raw[current]['tokens'][7]['value']:endpoints.reverse()
            vertices.append(endpoints[0])
            cycle.append(current)
            current = pointer(current,3,'coedge')
        assert current==cycle[0] and len(set(vertices))==4
        plane = pointer(face,7,'plane-surface')
        origin,normal = raw[plane]['tokens'][3]['value'],raw[plane]['tokens'][4]['value']
        points = [scaled[v] for v in vertices]
        mathematical = cross(sub(points[1],points[0]),sub(points[3],points[0]))
        length = math.hypot(*mathematical)
        mathematical = [v/length for v in mathematical]
        assert math.isclose(abs(dot(mathematical,normal)),1.,rel_tol=0.,abs_tol=1e-8)
        residuals = [dot(normal,sub(point,origin)) for point in points]
        assert all(math.isfinite(v) and abs(v)<1e-8 for v in residuals)
        assert set(vertices)==set(published['derived_planar_quad']['vertex_cycle'])
        for evidence in published['boundary_point_correspondence']:
            near(evidence['derived_scaled_position_cm'],scaled[evidence['vertex_index']])
        if set(vertices)==set(bottom.values()):cap_cycle=vertices
        plane_proofs.append(dict(face_index=face,plane_record_index=plane,
            independently_followed_coedge_cycle=cycle,fixed_vertex_cycle=vertices,
            independent_plane_point_residuals=residuals,
            raw_FACE_flag=raw[face]['tokens'][8]['value'],raw_Plane_v_flag=raw[plane]['tokens'][6]['value'],
            flag_or_native_UV_interpretation=None))
    assert cap_cycle is not None
    cap = [source[v] for v in cap_cycle]
    area_vector = [sum(cross(sub(cap[i],cap[0]),sub(cap[(i+1)%4],cap[0]))[j] for i in range(4))/2 for j in range(3)]
    source_volume = abs(dot(area_vector,translation))
    scaled_volume = source_volume*math.prod(factors)
    assert math.isclose(source_volume,group['derived_prism']['source_prism']['volume_cm3'],abs_tol=1e-9)
    assert math.isclose(scaled_volume,group['derived_prism']['scaled_prism']['volume_cm3'],abs_tol=1e-9)
    literal = group['literal_source_like_cache_corroboration']
    assert literal['same_stored_BODY_identifier']==group['body_binding']['stored_handle']
    assert literal['qualified_historical_state'] is literal['source_before_Scale_identity'] is None
    assert len(literal['full_FACE_name_observations'])==6
    for observation in literal['full_FACE_name_observations']:
        assert observation['numeric_component_identity'] is None
        for item in ('initial_FACE','view_FACE'):
            for attribute in observation[item]['full_generic_attributes']:
                assert bytes.fromhex(attribute['payload_hex'])==blob[attribute['payload_offset']:attribute['payload_end_offset']]
    for evidence in literal['derived_source_vertex_correspondence']:
        near(source[evidence['initial_vertex_index']],evidence['literal_view_raw_position'])
        near(source[evidence['initial_vertex_index']],evidence['derived_source_position_cm'])
    center_proof = group['vertex_center_literal_view_correspondence']
    if center_proof is not None:
        near(center,center_proof['independently_derived_source_center_cm'])
        vertex = center_proof['initial_cache_vertex_literal_correspondence']['initial_vertex_index']
        near(center,source[vertex])
        assert center_proof['initial_selected_vertex_identity'] is center_proof['API_handle_identity'] is None
    return dict(native_body_object_id=group['source_native_body_object_id'],asm_body_index=body_id,
        native_POINT_to_cache_vertex_derivations=point_rows,
        independent_straight_parameter_samples=line_samples,independent_planar_boundary_proofs=plane_proofs,
        independently_derived_source_volume_cm3=source_volume,independently_derived_scaled_volume_cm3=scaled_volume,
        same_ID_literal_view_corroborated=True,coordinate_identity_selection=False)


def validate(zstd,baseline_path):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit']=='fb2865a' and baseline['files']==list(FILES)
    old = {Path(row['file']).relative_to(ROOT).as_posix():row for row in baseline['before']}
    report = dict(samples=[],guards=[],positive_controls=[],API_context=[],checks=[])
    totals = Counter()
    contexts = {}
    saved = None
    def check(label,condition):
        if not condition:raise AssertionError(label)
        report['checks'].append(label)
    for archive in FILES:
        data,records,features,member,members = load(ROOT,archive,zstd)
        stream = old[archive]['streams'][0]
        bindings = stream['body_blob_bindings']
        before = copy.deepcopy((features,records,bindings,members))
        summary = decode_scale_reconstruction(data,records,features,member,members,bindings)
        check(archive+' all caller inputs unchanged',(features,records,bindings,members)==before)
        proofs = []
        if archive in FILES[:7]:
            check(archive+' one qualified owner with no stale diagnostics',len(summary['decoded'])==1 and not summary['unresolved'])
            row = summary['decoded'][0]
            check(archive+' no invented Scale result anchor',row['scale_owned_result_anchor_object_ids']==[])
            for group in row['derived_prism_groups']:
                proofs.append(independent_prism(data,records,members,row,group))
                totals.update(prism_groups=1,source_vertices=8,scaled_vertices=8,source_segments=12,
                    scaled_segments=12,source_planar_quads=6,scaled_planar_quads=6,
                    finite_EDGE_endpoints=24,FACE_boundary_points=24,literal_source_like_vertex_comparisons=8,
                    independent_Line_parameter_samples=36)
                if saved is None:saved=(archive,data,records,features,member,members,bindings,summary)
            totals['qualified_Scale_features']+=1
            truth_path = ROOT/Path(archive).parent/'ground_truth.json'
            truth = json.loads(truth_path.read_text())
            actual = next(s for s in truth['samples'] if s['file']==Path(archive).name)
            settings = row['native_source_provenance']['settings']
            if 'settings' in actual:
                api = actual['settings']
                check(archive+' actual saved Scale factors agree',api['is_uniform']==settings['is_uniform']
                    and ([api['factor']]*3 if api['is_uniform'] else api['factors'])==settings['factors_xyz'])
                point = actual.get('actual_point',{})
                center = point.get('position_cm',api.get('point_cm'))
                if center is not None:near(center,settings['reconstruction_center_cm'])
            else:
                factor = next(p['value'] for p in actual['parameters'] if p['role']=='ScaleFactor')
                check(archive+' actual saved ModelParameter ScaleFactor agrees',settings['factors_xyz']==[factor]*3)
            report['API_context'].append(dict(archive=archive,ground_truth_sha256=sha(truth_path),
                actual_saved_settings=actual.get('settings'),actual_saved_point=actual.get('actual_point'),
                actual_saved_parameters=actual.get('parameters'),
                scope='Saved controls/center corroboration after typed native source qualification; no API/native point identity by coordinates'))
            if archive in FILES[1:3]:
                api_path = ROOT/'bodycoords-2c2aa8982ad4/ground_truth.json'
                api = next(s for s in json.loads(api_path.read_text())['samples'] if s['source']==archive)
                placement, = api['placements']
                points = row['derived_prism_groups'][0]['derived_prism']['vertices']
                actual_set = sorted(tuple(round(v,12) for v in p) for p in placement['world_vertex_positions_cm'])
                predicted_set = sorted(tuple(round(v,12) for v in p['scaled_position_cm']) for p in points)
                check(archive+' independent saved API root vertex set agrees after native identities',actual_set==predicted_set)
                report['API_context'].append(dict(archive=archive,ground_truth_sha256=sha(api_path),
                    actual_API_root_vertex_set_cm=placement['world_vertex_positions_cm'],
                    independently_derived_vertex_set_cm=[p['scaled_position_cm'] for p in points],
                    API_per_vertex_assignment=None,scope='Whole root BODY point sets only, after native identity/affine proof; API collection order never selects identities'))
                totals['independent_API_root_vertex_set_controls']+=1
        elif archive in FILES[7:10]:
            check(archive+' explicit unsupported actual Scale diagnostic',not summary['decoded'] and len(summary['unresolved'])==1)
            totals['explicit_unsupported_Scale_controls']+=1
        else:
            check(archive+' unrelated helper summary empty',not summary['decoded'] and not summary['unresolved'])
            totals['unrelated_empty_controls']+=1
        report['samples'].append(dict(archive=archive,archive_sha256=sha(ROOT/archive),expected_summary=summary,
            independently_recomputed_geometry=proofs,caller_inputs_unchanged=True))
        contexts[archive]=(data,records,features,member,members,bindings,summary)
    archive,data,records,features,member,members,bindings,summary = saved
    group = summary['decoded'][0]['derived_prism_groups'][0]
    blob_member = group['history_blob_member']
    blob = members[blob_member]
    parsed = inspect_asm(blob)
    def altered_blob(record,field,transform):
        changed = bytearray(blob)
        token = parsed['records'][record]['tokens'][field]
        value = transform(copy.deepcopy(token['value']))
        if isinstance(value,list):struct.pack_into('<3d',changed,token['offset']+1,*value)
        elif type(value) is bool:changed[token['offset']]=10 if value else 11
        elif token['tag'] in (4,12):struct.pack_into('<q',changed,token['offset']+1,value)
        else:struct.pack_into('<d',changed,token['offset']+1,value)
        return bytes(changed)
    def run_blob(changed):
        mm = dict(members);mm[blob_member]=changed
        return decode_scale_reconstruction(data,records,features,member,mm,bindings)
    def reject(label,changed):
        answer = run_blob(changed)
        check(label,not answer['decoded'] and len(answer['unresolved'])==1)
        report['guards'].append(dict(guard=label,rejected=True,reason=answer['unresolved'][0]['reason']))
    first_point = group['vertex_correspondence'][0]['point_index']
    reject('Cache point shifted while native Sketch/Scale controls unchanged',
        altered_blob(first_point,3,lambda v:[v[0]+.125,v[1],v[2]]))
    line = group['native_straight_carrier_correspondence'][0]['native_Line']
    direction = line['direction'];axis = next(i for i in range(3) if direction[i]==0)
    def shift_axis(vector):vector[axis]+=.125;return vector
    reject('Straight carrier moved off its identity-fixed segment',altered_blob(line['index'],3,shift_axis))
    plane = group['native_planar_boundary_correspondence'][0]['native_Plane']
    reject('Plane carrier moved off fixed quad despite unchanged vertices',
        altered_blob(plane['index'],3,lambda v:[x+.125*n for x,n in zip(v,plane['normal'])]))
    edge = group['native_straight_carrier_correspondence'][0]['edge_index']
    reject('Finite EDGE domain endpoint changed with carrier and vertices unchanged',altered_blob(edge,6,lambda v:v+.125))
    profile_edge_ids = {p['cached_profile_edge_record_index']
        for p in group['identity_provenance']['profile_line_edge_proofs']}
    other_edge = next(e['edge_index'] for e in group['identity_provenance']['edge_vertex_pairs']
        if e['edge_index'] not in profile_edge_ids)
    other_coedge = next(r['index'] for r in parsed['records'] if r['section']=='geometry'
        and r['name']=='coedge' and r['tokens'][6]['value']==other_edge)
    reject('Nonprofile EDGE self-partner cannot qualify a closed prism',
        altered_blob(other_coedge,5,lambda value:other_coedge))
    foreign_coedge = next(r['index'] for r in parsed['records'] if r['section']=='geometry'
        and r['name']=='coedge' and r['tokens'][6]['value']!=other_edge)
    reject('Nonprofile EDGE first-coedge head must belong to its two uses',
        altered_blob(other_edge,7,lambda value:foreign_coedge))
    vertex = group['vertex_correspondence'][0]['vertex_index']
    foreign_edge = next(r['index'] for r in parsed['records'] if r['section']=='geometry'
        and r['name']=='edge' and vertex not in (r['tokens'][3]['value'],r['tokens'][5]['value']))
    reject('VERTEX first-edge head must be incident in the full prism',
        altered_blob(vertex,3,lambda value:foreign_edge))
    body_pair = group['literal_source_like_cache_corroboration']['literal_source_body_pair']
    reject('Literal source BODY pair changes explicitly mapped stored identifier',
        altered_blob(body_pair['side0_inspection_record_index'],1,lambda v:v+100))
    profile = summary['decoded'][0]['native_source_provenance']['source_groups'][0]['profile_cache_correspondence']
    tag_record = profile['source_curves'][0]['cached_coedge_candidates'][0]['attribute_record_index']
    text_token = parsed['records'][tag_record]['tokens'][9]
    old_text = text_token['value']
    new_text = str(profile['source_curves'][1]['native_entity_tag'])+' '+' '.join(old_text.split()[1:])
    assert len(new_text)==len(old_text)
    changed = bytearray(blob)
    changed[text_token['offset']+2:text_token['offset']+2+len(old_text)]=new_text.encode()
    reject('One profile tag redirected without coordinate fallback',bytes(changed))
    face_tag = group['complete_signed_FACE_naming'][0]['full_generic_attributes'][0]
    name_token = next(t for t in parsed['records'][face_tag['attribute_record_index']]['tokens']
        if t['kind']=='string' and t['value']==face_tag['terms'][0]['name'])
    other_name = group['complete_signed_FACE_naming'][1]['complete_terms'][0]['name']
    assert len(other_name)==len(name_token['value'])
    changed = bytearray(blob)
    changed[name_token['offset']+2:name_token['offset']+2+len(other_name)]=other_name.encode()
    reject('Duplicate complete FACE name groups remain ambiguous',bytes(changed))
    def math_projection(answer):
        return [[g['derived_prism'] for g in row['derived_prism_groups']] for row in answer['decoded']]
    # Harmless caller annotations cannot replace the source helper's fresh
    # native Sketch/parameter/placement decoding.
    annotated = copy.deepcopy(features)
    sketch = next(f for f in annotated if f['kind']=='Sketch')
    sketch['geometry']=[dict(kind='Point',object_id=999999,position_cm=[999.,999.,999.])]
    answer = decode_scale_reconstruction(data,records,annotated,member,members,bindings)
    check('Caller Sketch geometry annotations cannot construct the source prism',answer==summary)
    report['positive_controls'].append(dict(control='Harmless false caller Sketch geometry',complete_summary_exact=True))
    negative = next(t for t in parsed['records'][face_tag['attribute_record_index']]['tokens']
        if t['tag']==4 and t['value']<0 and t['value']!=-1)
    answer = run_blob(altered_blob(face_tag['attribute_record_index'],
        parsed['records'][face_tag['attribute_record_index']]['tokens'].index(negative),lambda v:-999))
    check('Opaque signed naming suffix is retained without feature-ID meaning',
        len(answer['decoded'])==1 and not answer['unresolved'] and math_projection(answer)==math_projection(summary))
    report['positive_controls'].append(dict(control='Signed FACE component changed to-999',
        derived_geometry_exact=True,numeric_component_identity=None))
    for label,record,field in [('Plane v flag',plane['index'],6),
                               ('FACE sense flag',group['native_planar_boundary_correspondence'][0]['face_index'],8)]:
        answer = run_blob(altered_blob(record,field,lambda value:not value))
        check(label+' retained literally without changing mathematical prism',
            len(answer['decoded'])==1 and not answer['unresolved'] and math_projection(answer)==math_projection(summary))
        report['positive_controls'].append(dict(control=label+' toggled',derived_geometry_exact=True,
            native_UV_or_FACE_orientation_semantics=None))
    check('Bounded actual coverage totals',totals['qualified_Scale_features']==7 and totals['prism_groups']==8
        and totals['source_vertices']==64 and totals['scaled_segments']==96 and totals['scaled_planar_quads']==48)
    report.update(interface='decode_scale_reconstruction(data,records,features,member,members,body_blob_bindings,body_selections=None)->decoded/unresolved/scope',
        integration=dict(stream='scale_reconstruction',feature_annotation='scale_reconstruction',
            feature_object_id_field='feature_object_id',old_settings_warnings_geometry_and_ASM_changes=0),
        baseline=dict(commit='fb2865a',path=str(baseline_path),sha256=sha(baseline_path)),
        validation=dict(totals,guards=len(report['guards']),positive_controls=len(report['positive_controls']),
            check_count=len(report['checks']),main_runs=0,live_calls=0,geometry_fits=0,
            native_UV_or_current_or_historical_identity_claims=0),
        source_sha256={name:sha(ROOT/name) for name in ('decode_scale_reconstruction.py',
            'validate_scale_reconstruction.py','decode_scale_reconstruction_sources.py','decode_scale_prism_geometry.py',
            'decode_profile_cache_correspondence.py','materialize_asm_literal_view.py','decode_asm_history.py',
            'decode_asm_recipe_tags.py','decode_brep.py','decode_body_asm_identifiers.py','decode_recipe_components.py')},
        limitations=['Original prism coordinates are derived from native Sketch point/Line references, frame and untapered Extrude controls; no cache coordinate constructs or fits them.',
            'All cache vertex/EDGE/FACE identities are fixed by native profile tags and topology before mathematical geometry comparisons.',
            'The same mapped native BODY is retained; no Scale-owned result anchor or serialized before/current state is invented.',
            'Literal journal views carry explicit same-ID BODY pairs and raw origins only; source-like geometry agreement assigns no chronology.',
            'Full signed FACE name components, raw flags and intervals are retained. Numeric suffixes, native UV signs and API collection order are not identity rules.',
            'Two saved API root vertex sets are collective corroboration only. Other saved API controls do not supply missing geometry or per-vertex native identity.',
            'Sketch-input and rational-Patch-source Scale fixtures remain explicitly unsupported; general taper, feature regeneration and arbitrary occurrence frames are outside scope.'])
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--zstd')
    parser.add_argument('--baseline-cache',type=Path,default=Path('/private/tmp/fusion-scale-reconstruction-baseline.json'))
    parser.add_argument('--output',default='scale-reconstruction-decoding.json')
    args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd,args.baseline_cache)
    Path(args.output).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report['validation'],sort_keys=True))
