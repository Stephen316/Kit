"""Native Mirror cache identities checked against a selected-plane reflection.

Owned selectors/anchors and complete FACE names fix every vertex correspondence
before the Householder matrix is computed. No matrix is fitted to coordinates.
"""
import math
import struct

from asm_records import inspect_asm
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_brep import decode_topology
from decode_circular_feature_caches import _face_names
from decode_circular_placement_evidence import _vertices
from decode_mirror_cache_sources import qualify_mirror_cache_sources
from decode_mirror_modes import MIRROR

SCOPE=('Observed noncombine BODY/single-or-two-Extrude Mirror source/result cache naming and typed '
       'vertex correspondence, checked against a selected-native-plane Householder reflection; '
       'computed verification only, without stored transforms, API/current/history placement or regeneration')


def _householder(plane):
    origin, normal = plane['origin'], plane['unit_normal']
    if (not isinstance(origin,(list,tuple)) or not isinstance(normal,(list,tuple))
            or len(origin)!=3 or len(normal)!=3
            or any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) for v in list(origin)+list(normal))):
        raise ValueError('Mirror selected plane frame is not a finite three-vector pair')
    norm=math.hypot(*normal)
    if not math.isclose(norm,1.,rel_tol=0.,abs_tol=1e-10):
        raise ValueError('Mirror selected plane normal is not independently normalized')
    rotation=[[float(i==j)-2*normal[i]*normal[j] for j in range(3)] for i in range(3)]
    dot=sum(a*b for a,b in zip(origin,normal));translation=[2*dot*n for n in normal]
    determinant=(rotation[0][0]*(rotation[1][1]*rotation[2][2]-rotation[1][2]*rotation[2][1])
        -rotation[0][1]*(rotation[1][0]*rotation[2][2]-rotation[1][2]*rotation[2][0])
        +rotation[0][2]*(rotation[1][0]*rotation[2][1]-rotation[1][1]*rotation[2][0]))
    if (any(not math.isfinite(v) for r in rotation for v in r) or any(not math.isfinite(v) for v in translation)
            or not math.isclose(determinant,-1.,rel_tol=0.,abs_tol=1e-9)
            or max(abs(sum(a*b for a,b in zip(rotation[i],rotation[j]))-float(i==j)) for i in range(3) for j in range(3))>1e-9):
        raise ValueError('Mirror selected plane does not produce a finite orthogonal determinant-minus-one reflection')
    return rotation,translation,[v for r,t in zip(rotation,translation) for v in r+[t]]+[0.,0.,0.,1.],determinant


def decode_mirror_cache_reflections(data,records,features,member,members,body_blob_bindings):
    """Return bounded native-source/cache/plane verification, without mutation."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    candidates=[f for f in features if f.get('class_guid')==MIRROR]
    if not candidates:return result
    grouped,metadata={},{}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    for feature in features:metadata.setdefault(feature['object_id'],[]).append(feature)
    joined=None;cached={}
    for feature in candidates:
        fid=feature['object_id']
        try:
            native=grouped.get(fid,[])
            if len(native)!=1 or native[0].class_guid!=MIRROR or len(metadata[fid])!=1:
                raise ValueError('Mirror reflection receiving native/metadata identity missing or ambiguous')
            source=qualify_mirror_cache_sources(data,records,features,member,members,body_blob_bindings,feature)
            if source is None:continue
            if source['feature_object_id']!=fid or source['input_kind'] not in ('Body','Feature'):
                raise ValueError('Mirror cache source factory returned a different native receiver/input family')
            sources=source['source_native_body_object_ids'];anchors=source['result_anchors']
            if (not isinstance(sources,list) or len(sources) not in (1,2) or len(set(sources))!=len(sources)
                    or any(type(n) is not int or n<=0 for n in sources)
                    or len(anchors)!=len(sources) or len({a['object_id'] for a in anchors})!=len(anchors)
                    or any(a['source_owner_object_id']!=fid for a in anchors)):
                raise ValueError('Mirror cache source/result cardinality or reciprocal result ownership differs')
            results=[a['native_body_object_id'] for a in anchors];native_ids=sources+results
            if len(set(native_ids))!=len(native_ids):
                raise ValueError('Mirror source/result native BODY identities overlap or repeat')
            if joined is None:joined=decode_body_asm_identifiers(data,records,member,members,body_blob_bindings)
            bindings={nid:[(m,b) for m in joined['decoded'] for b in m['bindings'] if b['native_body_object_id']==nid] for nid in native_ids}
            if any(len(v)!=1 for v in bindings.values()):
                raise ValueError('Mirror source/result BODY has no unique fresh same-asset stored-ID mapping')
            if len({(v[0][0]['mapping_record_object_id'],v[0][0]['history_blob_member']) for v in bindings.values()})!=1:
                raise ValueError('Mirror source/result BODY caches leave one explicit same-asset mapping')
            mapping=bindings[sources[0]][0][0];blob_member=mapping['history_blob_member']
            plane=source['selected_plane']
            if plane['kind']=='NamedBRepFaceCache' and plane['history_blob_member']!=blob_member:
                raise ValueError('Mirror named plane/source/result caches use different initial blobs')
            if blob_member not in cached:
                blob=members[blob_member];parsed=inspect_asm(blob);topology=decode_topology(parsed)
                if topology['unresolved']:raise ValueError('Mirror mapped initial topology has unresolved fields')
                cached[blob_member]=(blob,parsed,{g['body_index']:g for g in topology['body_graphs']},{n['index']:n for n in topology['nodes']})
            blob,parsed,graphs,nodes=cached[blob_member];bodies={}
            for nid in native_ids:
                binding=bindings[nid][0][1];graph=graphs.get(binding['asm_body_index'])
                if graph is None or not graph['body_transform_is_identity']:
                    raise ValueError('Mirror mapped BODY cache has no unique identity-transform graph')
                named=_face_names(blob,parsed,graph);names=named['names'];components={n['components'] for n in names.values()}
                if len(components)!=1:raise ValueError('Mirror BODY complete FACE naming components disagree')
                bodies[nid]=dict(binding=binding,graph=graph,names=names,components=next(iter(components)),proof=named['proof'])
            seeds={}
            for nid in sources:
                components=bodies[nid]['components']
                if len(components)!=1 or components[0] in seeds:
                    raise ValueError('Mirror source complete naming prefix is missing or ambiguous')
                seeds[components[0]]=nid
            pair=source['stored_instance_key_pair']
            if (not isinstance(pair,(list,tuple)) or len(pair)!=2 or any(type(v) is not int or v<=0 for v in pair) or pair[0]!=2):
                raise ValueError('Mirror stored two-value instance/naming-key framing differs')
            targets={};common=set()
            for anchor in anchors:
                nid=anchor['native_body_object_id'];components=bodies[nid]['components']
                if len(components)!=3 or components[0] not in seeds or components[2]!=pair[1] or components[0] in targets:
                    raise ValueError('Mirror owned result complete naming tuple has no unique source/native-key correspondence')
                common.add(components[1]);targets[components[0]]=anchor
            if len(common)!=1 or set(targets)!=set(seeds):
                raise ValueError('Mirror owned result/source prefix product is not an exact bijection')
            # The native ownership/name-prefix product is fixed before any
            # source/result vertex coordinates or selected-plane arithmetic.
            for body in bodies.values():
                body['vertices']=_vertices(body['graph'],nodes,body['names'])
                if any(not math.isfinite(v) for p in body['vertices'].values() for v in p['raw_position']):
                    raise ValueError('Mirror identity-fixed vertex coordinate is not finite')
            for prefix,anchor in targets.items():
                src=bodies[seeds[prefix]];dst=bodies[anchor['native_body_object_id']]
                if ({v['name_key'] for v in src['names'].values()}!={v['name_key'] for v in dst['names'].values()}
                        or set(src['vertices'])!=set(dst['vertices'])):
                    raise ValueError('Mirror complete inherited FACE/vertex incidence identities disagree')
            rotation,translation,matrix,determinant=_householder(plane)
            copies=[]
            for prefix,nid in seeds.items():
                anchor=targets[prefix];target_id=anchor['native_body_object_id'];src,dst=bodies[nid],bodies[target_id];correspondence=[]
                for signature in sorted(src['vertices']):
                    left,right=src['vertices'][signature],dst['vertices'][signature]
                    expected=[sum(a*b for a,b in zip(row,left['raw_position']))+t for row,t in zip(rotation,translation)]
                    if any(not math.isfinite(v) for v in expected):
                        raise ValueError('Mirror computed reflected vertex is not finite')
                    residual=math.dist(expected,right['raw_position'])
                    if not math.isfinite(residual) or residual>1e-8:
                        raise ValueError('Mirror selected-plane reflection disagrees with an identity-fixed cached vertex')
                    correspondence.append(dict(incident_face_name_keys=[list(k) for k in signature],source=left,target=right,
                        computed_reflected_source_position=expected,residual_raw=residual))
                copies.append(dict(source_native_body_object_id=nid,result_native_body_object_id=target_id,
                    result_body_anchor=anchor,source_body_binding=src['binding'],result_body_binding=dst['binding'],
                    stored_source_naming_prefix=list(src['components']),stored_result_face_naming_components=list(dst['components']),
                    matched_vertex_count=len(correspondence),maximum_vertex_residual_raw=max(p['residual_raw'] for p in correspondence),
                    vertex_correspondence=correspondence))
            result['decoded'].append(dict(feature_object_id=fid,input_kind=source['input_kind'],
                native_source_provenance=source,history_blob_member=blob_member,
                mapping_record_object_id=mapping['mapping_record_object_id'],mapping_owner_object_id=mapping['owner_object_id'],
                source_native_body_object_ids=sources,owned_result_anchor_object_ids=[a['object_id'] for a in anchors],
                stored_instance_key_pair=list(pair),uninterpreted_common_feature_naming_component=next(iter(common)),
                complete_source_result_prefix_bijection=True,
                complete_body_naming_proofs=[dict(native_body_object_id=nid,asm_body_index=bodies[nid]['binding']['asm_body_index'],
                    binding=bodies[nid]['binding'],proof=bodies[nid]['proof']) for nid in native_ids],
                computed_householder_matrix=matrix,computed_determinant=determinant,cache_body_copies=copies,
                matrix_source='Computed solely from the independently selected native plane after all vertex identities are fixed; no fitted or serialized matrix',
                coordinate_scope='One explicitly mapped initial ASM cache with identity BODY transforms and native component-plane proof; no occurrence/world/current/history placement claim',
                API_element_identity=None,persistent_topology_identity=None,current_placement=None,qualified_historical_state=None,
                cache_application='Verification only; computed matrices are not applied to stored geometry or runtime placement',scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
            result['unresolved'].append(dict(feature_object_id=fid,reason=str(error)))
    return result
