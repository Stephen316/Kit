"""Cross-family ordered API proof for current-mesh buffer5 group caches."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from fusion_archive import read_members
from fusion_metadata import design_records
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_face_group_caches import decode_mesh_face_group_caches
from decode_mesh_face_groups import decode_mesh_face_groups
from decode_mesh_plane_cuts import decode_mesh_plane_cuts
from validate_mesh_remesh import load as feature_load

CAPTURES = (
    ('meshcontrasts-10c2557c91a3','after_edit'),
    ('meshplanecuts-18f2683c83f5','component_meshes_after_cut'),
    ('meshreduces-780954a23308','component_meshes_after_reduce'),
    ('meshreduces-8f01528f7f21','component_meshes_after_reduce'),
    ('meshremeshes-f07f97514069','component_meshes_after_remesh'),
    ('meshconverts-4b42d39fb1d5','component_meshes_after_convert'),
    ('meshcombines-541ebb6cc93f','component_meshes_after_combine'),
    ('meshsmooths-56f38f13430a','component_meshes_after_smooth'),
    ('meshreversenormals-2bc2dd3780cc','component_meshes_after_reverse'),
    ('meshshells-f5a2d6730f62','component_meshes_after_shell'),
    ('meshfacegroups-0b682fa7d749','component_meshes_after_face_groups'))


def validate(root,zstd):
    checks,samples,guards,old_controls=[],[],[],[]
    def check(label,condition,**fields):
        if not condition:raise AssertionError(label)
        checks.append(dict(check=label,**fields))
    def load(archive):
        members=read_members(root/archive,zstd)
        member=next(k for k in members if k.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
        data=members[member]
        records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        return decode_mesh_contents_variants(data,records,member,members)
    prior_plane=json.loads((root/'mesh-plane-cut-decoding.json').read_text())
    total_rows=total_labels=0
    negative_count=0
    distributions={}
    for folder,field in CAPTURES:
        truth=json.loads((root/folder/'ground_truth.json').read_text())
        check(folder+' actual terminal capture exists',(root/folder/'complete.txt').is_file())
        for actual in truth['samples']:
            archive=folder+'/'+actual['file']
            check(archive+' exact archive export hash',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
            meshes=load(archive);before=copy.deepcopy(meshes)
            result=decode_mesh_face_group_caches(meshes)
            check(archive+' every qualified current native row decoded',len(result['decoded'])==len(meshes['decoded']) and not result['unresolved'])
            api_meshes=actual[field]['component_mesh_bodies'] if field=='after_edit' else actual[field]['meshes']
            evidence=[]
            if not result['decoded']:
                check(archive+' converted source is not promoted to current native mesh',folder.startswith('meshconverts-') and api_meshes==[] and len(meshes['unresolved'])==1 and meshes['unresolved'][0]['reason']=='Unobserved opt-in native mesh prefix')
                negative_count+=1
            for row in result['decoded']:
                native=next(m for m in meshes['decoded'] if m['mesh_object_id']==row['mesh_object_id'])
                matches=[m for m in api_meshes or [] if m['name']==native['name']]
                route='Unique saved current API custom-name agreement after typed native current mesh/asset route'
                if len(matches)!=1:
                    # Reuse the already qualified PlaneCut result graph and
                    # literal native/API collection order, before checking
                    # coordinates, index arrays or group values.
                    check(archive+' only known unnamed SplitBody result uses prior typed route',archive=='meshplanecuts-18f2683c83f5/split_body_minimal_fill.f3d' and native['mesh_object_id']==333 and native['name']=='')
                    loaded=feature_load(root,archive,zstd)
                    operation=decode_mesh_plane_cuts(*loaded,mesh_contents=meshes)
                    prior=next(s for s in prior_plane['samples'] if s['archive']==archive)
                    check(archive+' existing PlaneCut full typed result proof unchanged',operation==prior['expected_decoded'] and meshes==prior['expected_mesh_contents'])
                    additional=operation['decoded'][0]['settings']['explicit_additional_result_mesh']
                    check(archive+' explicit owner/result selection and native ordered collection precede API comparison',additional['mesh_object_id']==native['mesh_object_id'] and additional['asset_object_id']==native['asset_object_id'] and additional['native_feature_owner_selection']['mesh_object_id']==333 and native['collection_mesh_object_ids']==[213,333] and len(api_meshes)==2)
                    api=api_meshes[1]
                    route='Prior PlaneCut explicit additional-result selection/native ordered collection [213,333] and saved API collection position1; no fabricated name equality or persistent API-ID claim'
                else:api=matches[0]
                original=api['original_polygon_mesh'];geometry=native['geometry']
                check(archive+' '+str(row['mesh_object_id'])+' counted native current mesh membership',row['mesh_object_id'] in native['collection_mesh_object_ids'])
                check(archive+' '+str(row['mesh_object_id'])+' exact qualified asset identity',row['asset_object_id']==native['asset_object_id'] and row['asset_member']==native['asset_member'] and row['asset_fusion_uuid']==geometry['fusion_uuid'])
                check(archive+' '+str(row['mesh_object_id'])+' exact API triangle index order',geometry['triangle_node_indices']==original['triangleNodeIndices'])
                points=[v for p in geometry['component_node_coordinates_cm'] for v in p]
                api_points=original['nodeCoordinatesAsDouble']
                error=max(abs(a-b) for a,b in zip(points,api_points))
                check(archive+' '+str(row['mesh_object_id'])+' ordered native points corroborate saved API',len(points)==len(api_points) and error<1e-6,maximum_component_coordinate_discrepancy_cm=error)
                labels=row['decoded_triangle_face_group_temporary_ids']
                check(archive+' '+str(row['mesh_object_id'])+' exact ordered API temporary group IDs',labels==original['triangleFaceGroupTempIds'] and len(labels)==original['triangleCount'])
                check(archive+' '+str(row['mesh_object_id'])+' exact Int32 buffer5 replay',struct.pack('<'+'i'*len(labels),*row['stored_int32_forward_differences']).hex()==row['stored_payload_hex']==geometry['buffers'][5]['uncompressed_payload_hex'])
                check(archive+' '+str(row['mesh_object_id'])+' generic auxiliary diagnostics unchanged',5 in geometry['unresolved_buffers'])
                total_rows+=1;total_labels+=len(labels)
                key=str(len(geometry['stored_node_coordinates_float32']))+'/'+str(original['triangleCount'])
                distributions[key]=distributions.get(key,0)+1
                evidence.append(dict(mesh_object_id=row['mesh_object_id'],asset_object_id=row['asset_object_id'],
                    API_identity_comparison_scope=route,exact_API_triangle_index_order=True,
                    actual_API_triangle_face_group_temporary_ids=labels,
                    maximum_component_coordinate_discrepancy_cm=error))
                if folder.startswith('meshfacegroups-') and actual['case']=='fast_twenty_degrees':guard_source=copy.deepcopy(native)
            check(archive+' original hierarchy and all diagnostics not mutated',meshes==before)
            samples.append(dict(archive=archive,expected_decoded=result,actual_API_evidence=evidence,
                upstream_current_mesh_summary_sha256=hashlib.sha256(json.dumps(meshes,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                upstream_mesh_diagnostics=copy.deepcopy(meshes['unresolved'])))
    # Preserve the existing operation helper dictionaries independently; the
    # generic cache extension does not replace or alter their narrower schema.
    old=json.loads((root/'mesh-face-group-decoding.json').read_text())
    for sample in old['samples']:
        args=feature_load(root,sample['archive'],zstd);meshes=load(sample['archive'])
        current=decode_mesh_face_groups(*args,mesh_contents=meshes)
        check(sample['archive']+' old FaceGroups full dictionary exact',current==sample['expected_decoded'])
        check(sample['archive']+' old geometry hierarchy exact',meshes==sample['expected_mesh_contents'])
        old_controls.append(dict(archive=sample['archive'],expected_decoded_sha256=hashlib.sha256(json.dumps(current,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
    def guard(label,mutate):
        bad=copy.deepcopy(guard_source);mutate(bad)
        got=decode_mesh_face_group_caches({'decoded':[bad]})
        check(label,not got['decoded'] and len(got['unresolved'])==1)
        guards.append(dict(guard=label,reason=got['unresolved'][0]['reason']))
    guard('Reject nonmember source despite asset geometry',lambda m:m.__setitem__('collection_mesh_object_ids',[]))
    guard('Reject native asset UUID disagreement',lambda m:m.__setitem__('asset_fusion_uuid','wrong'))
    guard('Reject unknown geometry dimensions',lambda m:m['geometry']['stored_node_coordinates_float32'].append([0,0,0]))
    guard('Reject missing signed-difference descriptor field',lambda m:m['geometry']['buffers'][5].__setitem__('descriptor_hex','81a15401'))
    guard('Reject incomplete auxiliary declared-size prefix',lambda m:m['geometry']['buffers'][5].__setitem__('decompression_scope','Declared-size prefix only'))
    guard('Reject label count differs from triangle count',lambda m:m['geometry']['buffers'][5].__setitem__('uncompressed_size',36))
    guard('Reject negative decoded temporary IDs',lambda m:m['geometry']['buffers'][5].__setitem__('uncompressed_payload_hex',struct.pack('<8i',*([0]*7+[-1])).hex()))
    return dict(interface='decode_mesh_face_group_caches(mesh_contents) -> decoded/unresolved/scope; single-row decode_mesh_face_group_cache(mesh)',
        scope='Saved current native mesh summaries only, with independent actual API ordered triangle/group comparisons across10 mesh families; no retained-source promotion or shared geometry changes',
        archive_count=len(samples),qualified_current_mesh_row_count=total_rows,ordered_API_temporary_label_count=total_labels,
        converted_noncurrent_negative_archive_count=negative_count,check_count=len(checks),malformed_guard_count=len(guards),
        observed_dimension_row_counts=distributions,samples=samples,old_FaceGroups_dictionary_controls=old_controls,
        checks=checks,malformed_guards=guards,
        prior_PlaneCut_result_proof_sha256=hashlib.sha256((root/'mesh-plane-cut-decoding.json').read_bytes()).hexdigest(),
        limitations=['Only observed mesh dimensions and complete strict buffer5 descriptor/extent admitted',
            'SignedInt32 values are temporary cache labels, not persistent native face/group IDs',
            'Zero label meaning and other auxiliary buffers remain unresolved',
            'Current asset/native graph establishes identity before ordered numerical API comparisons',
            'Unnamed SplitBody row reuses prior explicit result/native collection order proof; API name equality not invented',
            'Converted retained source assets remain excluded with original current-mesh diagnostics',
            'No grouping algorithm, lifecycle or regeneration implemented'],
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'decode_mesh_face_group_caches.py','validate_mesh_face_group_caches.py','decode_mesh_face_groups.py',
            'decode_mesh_contents.py','decode_mesh_geometry_variants.py')})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='mesh-face-group-cache-decoding.json');args=parser.parse_args()
    result=validate(Path(__file__).resolve().parent,args.zstd_library)
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('archive_count','qualified_current_mesh_row_count','ordered_API_temporary_label_count','check_count','malformed_guard_count')}))

if __name__=='__main__':main()
