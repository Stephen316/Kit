"""Focused API-truth and malformed-reference checks for body-tool inputs."""
from pathlib import Path
import copy, hashlib, json, struct, sys
root = Path(__file__).resolve().parent
sys.path.insert(0,str(root))
from decode_basics import decode_basics
from decode_body_tool_selections import decode_body_tool_selections
from decode_sketch import same
from fusion_archive import read_members
from fusion_metadata import design_records
z=next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
folder=root/'bodyselections-62e42366c722'
truth=json.loads((folder/'ground_truth.json').read_text())
assert len(truth['samples'])==4 and not truth['errors']
report={'fixture_folder':folder.name,'api_version':truth['fusion_version'],
        'decoder_sha256':hashlib.sha256((root/'decode_body_tool_selections.py').read_bytes()).hexdigest(),
        'interface':'decode_body_tool_selections(data, records, features, body_selections=None)',
        'validation_scope':'Four actual captures only; direct decoder handoff copies clear Scale tool_settings.point so the source-point branch is re-evaluated even after main-reader integration. No native source geometry or API truth is injected.',
        'samples':[],'negative_checks':[]}
cases={}
for sample in truth['samples']:
 assert not sample['getter_errors']
 archive=folder/sample['file'];main=decode_basics(archive,z)
 stream=next(s for s in main['streams'] if any(f['kind'] in ('Scale','Mirror','Shell') for f in s['features']))
 features=copy.deepcopy(stream['features'])
 feature=next(f for f in features if f['kind'] in ('Scale','Mirror','Shell'))
 if feature['kind']=='Scale': feature['tool_settings']['point']=None
 members=read_members(archive,z);data=members[stream['member']]
 records,_=design_records(data,members.get(stream['member'].replace('BulkStream.dat','MetaStream.dat')))
 by={r.object_id:r for r in records if r.is_primary}
 out=decode_body_tool_selections(data,records,features)
 assert len(out['decoded'])==1 and not out['unresolved'],(sample['file'],out)
 item=out['decoded'][0];settings=item['settings'];selected=settings['input_selections']
 names={b['object_id']:b['name'] for b in stream['body_properties']['bodies']}
 actual=sample['actual_inputs']
 kinds=['adsk::fusion::BRep'+{'Body':'Body','Face':'Face'}[s['kind']] for s in selected]
 decoded_names=[names[s['native_body_object_id']] for s in selected]
 checks={'actual_source_types_and_order_match':kinds==[a['entity_type'] for a in actual],
         'ordered_historical_body_names_match':decoded_names==[a['body_name'] for a in actual],
         'input_count_matches_actual':settings['input_count']==len(actual),
         'body_count_matches_actual':settings['input_body_count']==sum(a['entity_type'].endswith('BRepBody') for a in actual),
         'face_count_matches_actual':settings['input_face_count']==sum(a['entity_type'].endswith('BRepFace') for a in actual),
         'ordered_descriptor_ids_are_unique':len({s['descriptor_object_id'] for s in selected})==len(selected),
         'no_unresolved_inputs':not out['unresolved'] and 'unresolved_point' not in item}
 if feature['kind']=='Scale':
  p=settings['point'];api=sample['actual_point']
  checks.update(point_kind_matches_actual=api['entity_type']=='adsk::fusion::'+p['entity']['kind'],
                point_coordinates_match_actual=same(p['entity']['position_cm'],api['position_cm']),
                point_sketch_name_matches_actual=p['entity']['sketch_name']==api['sketch_name'],
                explicit_point_leaf_class=by[p['terminal_object_id']].class_guid=='D95DBAC0-238B-4429-A0AD-4AE5BEE79ADF')
  mainfeature=next(f for f in stream['features'] if f['object_id']==feature['object_id'])
  checks['main_reader_point_agrees_with_standalone']=mainfeature['tool_settings'].get('point')==p
 if settings['input_face_count']:
  checks['face_inputs_retain_bounded_recipes']=all(s['recipe']['payload_kind']=='bounded_face_recipe_data' for s in selected)
  checks['two_faces_are_not_two_body_inputs']=settings['input_face_count']==2 and settings['input_body_count']==0 and len(settings['native_input_body_object_ids'])==1
 assert all(checks.values()),(sample['file'],checks)
 report['samples'].append({'archive':str(archive.relative_to(root)),'feature_object_id':feature['object_id'],'feature_kind':feature['kind'],
                           'checks':checks,'decoded_input_types':kinds,'decoded_ordered_body_names':decoded_names,
                           'actual_inputs':[{'entity_type':a['entity_type'],'body_name':a['body_name']} for a in actual],
                           'decoded':item,'actual_point':sample.get('actual_point'),
                           'identity_scope':'Exact stored descriptor/owner references and independently corroborated historical body names; persistent ASM face identities and resulting-body lifecycle remain unresolved'})
 cases[feature['kind']+('_faces' if settings['input_face_count'] else '')]=(data,records,features,by,out)

def check_mutation(case,label,offset,replacement,preserve_bodies=False):
 data,records,features,by,baseline=cases[case]
 changed=bytearray(data);changed[offset:offset+len(replacement)]=replacement
 out=decode_body_tool_selections(bytes(changed),records,copy.deepcopy(features))
 if preserve_bodies:
  passed=(not out['unresolved'] and len(out['decoded'])==1 and 'unresolved_point' in out['decoded'][0]
          and 'point' not in out['decoded'][0]['settings']
          and out['decoded'][0]['settings']['input_selections']==baseline['decoded'][0]['settings']['input_selections']
          and out['decoded'][0]['settings']['input_body_count']==2)
  reason=out['decoded'][0].get('unresolved_point',{}).get('reason') if out['decoded'] else None
 else:
  passed=not out['decoded'] and len(out['unresolved'])==1
  reason=out['unresolved'][0]['reason'] if out['unresolved'] else None
 assert passed,(label,out)
 report['negative_checks'].append({'check':label,'passed':passed,'absolute_mutated_offset':offset,'replacement_hex':replacement.hex(),
                                   'expected_behavior':'Input bodies retained; unresolved_point records failure' if preserve_bodies else 'Feature input selection rejected',
                                   'reason':reason})

data,records,features,by,out=cases['Scale'];fields=out['decoded'][0]['settings']
proxy=by[fields['input_selection_record_object_ids'][0]]
check_mutation('Scale','Scale input proxy wrong owner',proxy.end-10,struct.pack('<Q',999999))
leaf=by[fields['point']['terminal_object_id']]
check_mutation('Scale','Scale source point tag absent; retain two input bodies',leaf.body+10,struct.pack('<Q',999999),True)
data,records,features,by,out=cases['Mirror'];collection=by[out['decoded'][0]['settings']['input_entity_collection_object_id']]
check_mutation('Mirror','Mirror collection count disagrees with bounded payload',collection.body+6,struct.pack('<I',3))
data,records,features,by,out=cases['Shell_faces'];proxy=by[out['decoded'][0]['settings']['input_selection_record_object_ids'][0]]
check_mutation('Shell_faces','Shell face proxy wrong owner',proxy.end-10,struct.pack('<Q',999999))
report['coverage']={'actual_captures':4,'decoded_body_input_references':5,'decoded_face_input_references':2,'decoded_sketch_points':1,'negative_guards':4}
report['limitations']=['Selection source types and ordering are validated against actual API getters; source topology recipes do not establish persistent ASM face identity.',
                       'Names corroborate native historical body anchors; they do not establish current resulting-body lifecycle.',
                       'Only captured root-context Scale/Mirror/Shell input forms are checked; arbitrary occurrence contexts remain unsupported.',
                       'Point-tag corruption is isolated: input bodies survive and unresolved_point is reported; no point coordinate is fabricated.']
report['validation_invocation']='/usr/bin/python3 validate_body_tool_selections.py'
output=root/'body-tool-selection-decoding.json';output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'output':str(output),'captures':len(report['samples']),'negative_checks':len(report['negative_checks']),'checks':sum(len(s['checks']) for s in report['samples'])}))
