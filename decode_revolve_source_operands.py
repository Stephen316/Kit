"""Fresh whole-profile solid angular Revolve inputs and selected-axis provenance.

Native controls and selected axis direction are preserved. Effective mathematical
rotation orientation is derived by a separate source-only constructor, never
chosen by target cache geometry. No chronology or persistent/API identity follows
from the creator-owned BODY and explicit same-asset stored-ID association.
"""
import copy
import math
import struct
import uuid

from decode_assembly import decode_assembly,SKETCH_BASE_GUID
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_properties import BODY,COLLECTION,decode_body_properties
from decode_body_selections import ANCHOR,decode_body_selections
from decode_construction_modes import decode_construction_modes
from decode_dependencies import decode_dependencies
from decode_parameters import decode_stream,read_string
from decode_placement import decode_placement,rigid_matrix,transform_point,transform_vector
from decode_profiles import PROFILE_DESCRIPTOR_GUID,PROFILE_LOOP_GUID,read_loops
from decode_revolve import decode_revolve
from decode_revolve_axes import decode_revolve_axes
from decode_selection import decode_selections,native_proxy_references
from decode_selection_recipe_incidence import decode_selection_recipe_incidence
from decode_sketch import attributes,decode_sketches,numbers,reference

REVOLVE='E3849A15-2FC6-42A0-AF3A-2F1D7273B406'
LINE='DCA267ED-D615-4934-B64F-AD805E8003E2'
CIRCLE='F0130424-8B7E-4092-93C9-1CA807482534'
POINT='C2CEDAE7-1716-47C1-B7B1-07B70081D0FB'
SKETCH='44A64366-4BD3-4B24-881A-F94C206E8F2D'
COMPONENT='E03784ED-5E19-4E14-B9F2-3B07017018CD'
NATIVE_AXIS='19031004-3AB6-4D13-ABBF-C51EE214688D'
SCOPE=('Observed solid unprojected NewBody angular Revolve with whole native four/three-Line, Circle or '
    'semicircle-plus-diameter profile; fresh POINT/curve/frame/component/creator-BODY/stored-ID proof, '
    'origin/custom two-POINT/SketchLine axes or exact-recipe-qualified source BRep Line. Native axis '
    'direction and signed along/against angles remain unchanged; effective rotation, constructed material '
    'and target cache corroboration are separate. No API/persistent identity or chronological state is inferred.')
TOL=1e-9


def qualify_revolve_source_operands(data,records,features,member,members,body_blob_bindings,feature):
    if feature.get('class_guid')!=REVOLVE:return None
    grouped={}
    for r in records:
        if r.is_primary:grouped.setdefault(r.object_id,[]).append(r)
    if any(len(rows)!=1 for rows in grouped.values()):
        raise ValueError('Revolve source duplicate primary namespace')
    def typed(identity,guid=None):
        rows=grouped.get(identity,[])
        if len(rows)!=1 or guid is not None and rows[0].class_guid!=guid:
            raise ValueError('Revolve source typed native identity missing, ambiguous or wrong class')
        r=rows[0];return r,data[r.body:r.end]
    def raw(identity,guid=None):
        r,p=typed(identity,guid)
        return dict(object_id=identity,class_guid=r.class_guid,record_offset=r.start,body_offset=r.body,end_offset=r.end,payload_hex=p.hex())
    receiver=feature['object_id'];record,body=typed(receiver,REVOLVE)
    supplied=[f for f in features if f['object_id']==receiver]
    if (len(supplied)!=1 or feature.get('record_offset')!=record.start or supplied[0].get('class_guid')!=REVOLVE
            or member not in members or members[member]!=data or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat')):
        raise ValueError('Revolve source receiving metadata or native member scope differs')
    from decode_basics import named_features,attach_parameters,sketch_references
    private=named_features(data,records);parameters,_=decode_stream(data,records);attach_parameters(data,records,private,parameters)
    decode_sketches(data,records,private);decode_placement(data,records,private)
    assembly=decode_assembly(data,records,private);properties=decode_body_properties(data,records,assembly)
    sketch_references(data,records,private)
    rows=[f for f in private if f['object_id']==receiver]
    if len(rows)!=1:raise ValueError('Revolve source fresh receiving metadata missing or ambiguous')
    fresh=rows[0];keys=('binding_object_id','parameter_object_id','role','raw_float64','display_units')
    if ([{k:p.get(k) for k in keys} for p in supplied[0].get('parameters',[])]!=
            [{k:p.get(k) for k in keys} for p in fresh['parameters']]):
        raise ValueError('Revolve source supplied parameters disagree with fresh reciprocal native bindings')
    controls=decode_revolve(body,fresh);rev=controls['revolve']
    if (controls['operation']['kind']!='NewBody' or controls['is_solid'] is not True or controls['is_project_axis'] is not False
            or rev['extent_kind']!='Angle' or rev['mode'] not in ('OneSided','Symmetric','TwoSided')):
        raise ValueError('Revolve reconstruction requires solid unprojected NewBody angular controls')
    angles=[rev['angle_radians']]+([rev['against_angle_radians']] if rev['mode']!='OneSided' else [])
    if any(not math.isfinite(a) or abs(a)<=TOL or abs(a)>2*math.pi+TOL for a in angles):
        raise ValueError('Revolve source active signed angular operands outside finite captured family')
    selection_summary=decode_body_selections(data,records)
    anchors=[a for a in selection_summary['body_anchors'] if a['source_owner_object_id']==receiver]
    if len(anchors)!=1:raise ValueError('Revolve source requires one unique creator-owned BODY anchor')
    anchor=anchors[0];native=anchor['native_body_object_id'];anchor_id=anchor['object_id'];typed(native,BODY)
    _,anchor_body=typed(anchor_id,ANCHOR)
    if len(anchor_body)!=102 or reference(anchor_body,80)!=native or reference(anchor_body,91)!=receiver:
        raise ValueError('Revolve source creator/anchor/BODY reciprocity differs')
    binding_input=dict(decoded=[dict(mapping_record_object_id=m['mapping_record_object_id'],owner_object_id=m['owner_object_id'],
        history_blob_member=m['history_blob_member'],body_count=m['body_count'],bindings=[dict(stored_handle=b['stored_handle'],
            native_body_object_id=b['native_body_object_id']) for b in m['bindings']]) for m in body_blob_bindings.get('decoded',[])])
    mappings=decode_body_asm_identifiers(data,records,member,members,binding_input)
    mapped=[(m,b) for m in mappings['decoded'] for b in m['bindings'] if b['native_body_object_id']==native]
    if len(mapped)!=1:raise ValueError('Revolve source creator BODY lacks unique same-asset stored-ID mapping')
    mapping,binding=mapped[0]
    descriptors=[]
    for rows in grouped.values():
        r=rows[0]
        if r.class_guid==PROFILE_DESCRIPTOR_GUID:
            p=data[r.body:r.end]
            if len(p)>=17 and reference(p,len(p)-11)==receiver:descriptors.append((r,p))
    if len(descriptors)!=1:raise ValueError('Revolve source requires one explicitly owned profile descriptor')
    descriptor,db=descriptors[0]
    if db[:2]!=bytes(2) or struct.unpack_from('<I',db,13)[0]!=1:
        raise ValueError('Revolve source profile descriptor prefix/count differs')
    namespace,cursor=read_string(db,17);sketch_text,_=read_string(db,cursor)
    if len(namespace)!=36 or not sketch_text.isascii() or not sketch_text.isdecimal():
        raise ValueError('Revolve source explicit profile Sketch namespace differs')
    uuid.UUID(namespace);sketch_id=int(sketch_text);typed(sketch_id,SKETCH)
    sketches=[f for f in private if f['kind']=='Sketch' and f['sketch_object_id']==sketch_id]
    if len(sketches)!=1:raise ValueError('Revolve source profile Sketch missing or ambiguous')
    sketch=sketches[0];definition_id=reference(db,2);_,definition=typed(definition_id,PROFILE_LOOP_GUID)
    loops=read_loops(definition,descriptor.object_id,sketch)
    if len(loops)!=1 or loops[0]['is_outer'] is not True:
        raise ValueError('Revolve source requires one complete whole-reference outer profile')
    refs=loops[0]['curve_references'];ids=[r['entity_id'] for r in refs]
    if len(set(ids))!=len(ids) or any(r['entity_kind'] not in ('Line','Circle','Arc') for r in refs):
        raise ValueError('Revolve source whole profile repeats or uses unsupported primitives')
    frame_cache={}
    def frame(s):
        identity=s['sketch_object_id']
        if identity in frame_cache:return frame_cache[identity]
        typed(identity,SKETCH)
        bases=[r for r in records if not r.is_primary and r.object_id==identity and r.class_guid==SKETCH_BASE_GUID]
        if len(bases)!=1:raise ValueError('Revolve source native Sketch base ambiguous')
        base=bases[0];p=data[base.body:base.end];transform_id=reference(p,0)
        tr,tb=typed(transform_id,'F47A46FB-DA27-4AFA-8A72-1B38FA596E23')
        matrix=rigid_matrix(s.get('placement',{}).get('sketch_to_component_matrix',[]))
        if (len(tb) not in (15,143) or tb[:2]!=bytes(2) or tb[-12]!=0
                or len(tb)==15 and tb[:4]!=bytes.fromhex('00000100')
                or len(tb)==143 and (tb[2]!=0 or numbers(tb,3,16)!=matrix)
                or s['placement'].get('transform_object_id')!=transform_id or s['placement'].get('record_offset')!=tr.start):
            raise ValueError('Revolve source canonical/native rigid Sketch frame differs')
        component=reference(tb,len(tb)-11);typed(component,COMPONENT)
        if s.get('component_object_id')!=component:
            raise ValueError('Revolve source Sketch collection/transform component differs')
        result=dict(component_object_id=component,sketch_base_record_offset=base.start,sketch_base_payload_hex=p.hex(),
            transform=raw(transform_id),canonical_placement=copy.deepcopy(s['placement']),
            collection_component_association=s['component_association'])
        frame_cache[identity]=result;return result
    profile_frame=frame(sketch);component=profile_frame['component_object_id']
    matrix=sketch['placement']['sketch_to_component_matrix']
    points={};primitives=[]
    def primitive(s,identity,kind,tag):
        _,p=typed(identity,LINE if kind=='Line' else CIRCLE);props,cursor=attributes(p,2)
        found=[g for g in s['geometry'] if g['object_id']==identity and g['kind']==kind]
        expected={'Line':171,'Circle':162,'Arc':182}[kind]
        if (len(found)!=1 or p[:2]!=b'\0\1' or len(p)-cursor!=expected or props.get('crv_primary_id')!=tag
                or props.get('crv_secondary_id')!=0 or reference(p,len(p)-11)!=s['sketch_object_id']):
            raise ValueError('Revolve source native primitive tag/frame/owner differs')
        g=found[0];values=numbers(p,cursor,12)
        if any(not math.isfinite(v) for v in values):raise ValueError('Revolve source native primitive coefficients are nonfinite')
        if kind=='Line':
            point_ids=[g['start_point_id'],g['end_point_id']]
            if reference(p,cursor+107)!=point_ids[0] or reference(p,cursor+96)!=point_ids[1]:
                raise ValueError('Revolve source Line endpoint IDs differ')
            geometry={k:copy.deepcopy(g[k]) for k in ('start_cm','end_cm')}
        else:
            point_ids=[g['center_point_id']]
            if reference(p,cursor+96)!=point_ids[0] or g['radius_cm']<=0:
                raise ValueError('Revolve source Circle centre/radius differs')
            geometry={k:copy.deepcopy(g[k]) for k in ('center_cm','radius_cm','normal','reference_axis')}
            if (not math.isclose(math.hypot(*g['normal']),1.,abs_tol=TOL)
                    or not math.isclose(math.hypot(*g['reference_axis']),1.,abs_tol=TOL)
                    or abs(sum(a*b for a,b in zip(g['normal'],g['reference_axis'])))>TOL):
                raise ValueError('Revolve source Circle/Arc frame is not orthonormal')
            if kind=='Arc':
                point_ids += [g['start_point_id'],g['end_point_id']]
                if reference(p,cursor+118)!=point_ids[1] or reference(p,cursor+107)!=point_ids[2]:
                    raise ValueError('Revolve source Arc endpoint IDs differ')
                geometry.update(start_angle_radians=g['start_angle_radians'],end_angle_radians=g['end_angle_radians'],
                    start_cm=g['start_cm'],end_cm=g['end_cm'])
        native_points=[]
        for pid in point_ids:
            _,pb=typed(pid,POINT);pp,pc=attributes(pb,2);position=numbers(pb,pc+19,3)
            if (pb[:2]!=b'\0\1' or len(pb)-pc!=99 or 'pt_tag' not in pp
                    or reference(pb,len(pb)-11)!=s['sketch_object_id'] or any(not math.isfinite(v) for v in position)
                    or abs(position[2])>TOL):
                raise ValueError('Revolve source native POINT owner/frame differs')
            item=dict(point_object_id=pid,entity_tag=pp['pt_tag'],position_cm=position,native_record=raw(pid))
            native_points.append(item)
            if s['sketch_object_id']==sketch_id:points[pid]=item
        return dict(source_primitive_id=identity,kind=kind,entity_tag=tag,source_geometry=geometry,
            native_point_object_ids=point_ids,native_points=native_points,native_record=raw(identity))
    for ref in refs:primitives.append(primitive(sketch,ref['entity_id'],ref['entity_kind'],ref['entity_tag']))
    kinds=[p['kind'] for p in primitives];point_cycle=[];line_cycle=[]
    if kinds==['Circle']:
        family='Circle';mathematical_profile=dict(kind='Circle',**primitives[0]['source_geometry'])
    elif sorted(kinds)==['Arc','Line']:
        arc=next(p for p in primitives if p['kind']=='Arc');line=next(p for p in primitives if p['kind']=='Line')
        ap=arc['native_point_object_ids'][1:];lp=line['native_point_object_ids']
        g=arc['source_geometry'];a,b=g['start_angle_radians'],g['end_angle_radians']
        if set(ap)!=set(lp) or len(set(ap))!=2 or not math.isclose(abs(b-a),math.pi,abs_tol=TOL):
            raise ValueError('Revolve source Arc/diameter POINT incidence or semicircle interval differs')
        if math.dist(line['source_geometry']['start_cm'],line['source_geometry']['end_cm'])<=TOL:
            raise ValueError('Revolve source semicircle diameter degenerates')
        family='Semicircle';mathematical_profile=dict(kind='Semicircle',**{k:g[k] for k in ('center_cm','radius_cm','normal','reference_axis')},
            angle_interval_radians=[a,b],diameter_start_cm=line['source_geometry']['start_cm'],diameter_end_cm=line['source_geometry']['end_cm'])
    elif len(kinds) in (3,4) and set(kinds)=={'Line'}:
        mathematical_vertices=[];endpoint_roles={};role_points={}
        native_adjacency={}
        for p in primitives:
            pair=[]
            for identity in p['native_point_object_ids']:
                position=points[identity]['position_cm']
                matches=[i for i,q in enumerate(mathematical_vertices) if math.dist(position,q)<=TOL]
                if len(matches)>1:raise ValueError('Revolve source mathematical endpoint join ambiguous')
                if not matches:
                    matches=[len(mathematical_vertices)];mathematical_vertices.append(position)
                role=matches[0];pair.append(role);role_points.setdefault(role,[]).append(identity)
                native_adjacency.setdefault(identity,[]).append(p['source_primitive_id'])
            if pair[0]==pair[1]:raise ValueError('Revolve source polygon Line mathematically degenerates')
            endpoint_roles[p['source_primitive_id']]=pair
        adjacency={i:[] for i in range(len(mathematical_vertices))}
        for identity,(a,b) in endpoint_roles.items():
            adjacency[a].append((b,identity));adjacency[b].append((a,identity))
        if len(adjacency)!=len(primitives) or any(len(v)!=2 for v in adjacency.values()):
            raise ValueError('Revolve source source-only mathematical endpoint incidence is not degree two')
        current=min(adjacency);start=current;previous_line=None
        while current not in point_cycle:
            point_cycle.append(current);choices=[(p,l) for p,l in adjacency[current] if l!=previous_line]
            nxt,line_id=min(choices,key=lambda item:item[1]);line_cycle.append(line_id);current=nxt;previous_line=line_id
        if current!=start or len(point_cycle)!=len(primitives) or len(set(line_cycle))!=len(primitives):
            raise ValueError('Revolve source polygon has disconnected or ambiguous mathematical cycles')
        coordinates=[mathematical_vertices[i] for i in point_cycle]
        area=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(coordinates,coordinates[1:]+coordinates[:1]))/2
        if not math.isfinite(area) or abs(area)<=TOL:raise ValueError('Revolve source native polygon area degenerates')
        family='Triangle' if len(kinds)==3 else 'FourLinePolygon'
        mathematical_profile=dict(kind='Polygon',points_cm=coordinates)
    else:raise ValueError('Revolve source whole-profile primitive family outside captured rectangle/Circle/semicircle/triangle')
    # Common native controls remain untouched; copies are passed to the existing
    # selection codecs, which attach their own observations only to private rows.
    axis_features=copy.deepcopy(private);af=[f for f in axis_features if f['object_id']==receiver][0];af.update(copy.deepcopy(controls))
    axis_definitions=decode_construction_modes(data,records,axis_features)
    decode_selections(data,records,axis_features)
    direct=af['revolve'].get('axis')
    axis_rows=decode_revolve_axes(data,records,axis_features)
    if direct is None:
        chosen=[r['axis'] for r in axis_rows['decoded'] if r['feature_object_id']==receiver]
        if len(chosen)!=1:raise ValueError('Revolve source selected native axis unresolved')
        direct=chosen[0]
    axis=copy.deepcopy(direct);entity=axis['entity'];axis_id=rev['axis_selection_record_object_id']
    proxy_record,proxy=typed(axis_id,'2CA5A1CD-C99B-4C9B-91AF-57989148E841');descriptor_ids,attrs=native_proxy_references(data,proxy_record)
    if attrs or len(descriptor_ids)!=1 or reference(proxy,len(proxy)-11)!=receiver:
        raise ValueError('Revolve source receiving singleton axis proxy differs')
    axis_proof=dict(selection=axis,native_records=[raw(axis_id)],axis_component_object_id=component)
    dependency_ids=[receiver,sketch['object_id']];body_ids=[native]
    def support(identity,entries,repeated):
        _,p=typed(identity,'6CCF41D5-40BE-48ED-A834-18F3EAED6C57');n=len(entries)
        if (len(p)!=39+19*n or p[:12]!=bytes(6)+b'\1\1'+struct.pack('<I',n)
                or [reference(p,12+19*i) for i in range(n)]!=entries or reference(p,12+19*n)!=repeated or p[-8:]!=bytes(8)):
            raise ValueError('Revolve source axis support/backlink framing differs')
        axis_proof['native_records'].append(raw(identity))
    if entity['kind'] in ('ConstructionAxis','SketchLine'):
        descriptor_id=descriptor_ids[0];_,desc=typed(descriptor_id,'5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
        if len(desc)!=263 or desc[:2]!=bytes(2) or struct.unpack_from('<I',desc,13)[0]!=1 or reference(desc,252)!=receiver:
            raise ValueError('Revolve source whole-axis descriptor prefix/count/owner differs')
        ns,c=read_string(desc,17);text,c=read_string(desc,c);uuid.UUID(ns);uuid.UUID(text)
        if c!=169 or len(ns)!=36 or len(text)!=36 or desc[c:c+12]!=struct.pack('<QI',2,1):
            raise ValueError('Revolve source whole-axis namespace/context framing differs')
        context_id=reference(desc,181);_,context=typed(context_id,'50AEE8B4-9456-4DD7-847D-6F6C909BBB9D')
        if len(context)!=(85 if entity['kind']=='SketchLine' else 65):
            raise ValueError('Revolve source selected-axis context extent differs')
        for p,pos in ((proxy,68),(desc,226)):
            _,h=typed(reference(p,pos),'5FBE538E-139B-46D4-BCAF-CC796D1E1F78')
            if h!=bytes.fromhex('0001000000000000000000000000'):raise ValueError('Revolve source axis helper payload differs')
            axis_proof['native_records'].append(raw(reference(p,pos)))
        secondary=reference(proxy,23);_,sec=typed(secondary,'2DF7DA30-A4E4-4260-AFD1-D9C7154CB44B')
        if sec!=bytes.fromhex('0000010100'):raise ValueError('Revolve source axis proxy secondary framing differs')
        support(reference(proxy,82),[descriptor_id],axis_id)
        axis_proof['native_records'] += [raw(descriptor_id),raw(reference(desc,2)),raw(context_id),raw(secondary)]
        if entity['kind']=='SketchLine':
            axis_sketches=[s for s in private if s['kind']=='Sketch' and s['sketch_object_id']==entity['sketch_object_id']]
            if len(axis_sketches)!=1:raise ValueError('Revolve source selected-axis Sketch ambiguous')
            axis_sketch=axis_sketches[0];axis_frame=frame(axis_sketch)
            if axis_frame['component_object_id']!=component:raise ValueError('Revolve source axis/profile Sketch component differs')
            ap=primitive(axis_sketch,entity['object_id'],'Line',entity['entity_tag'])
            support(reference(desc,240),[axis_sketch['object_id'],descriptor_id],descriptor_id)
            axis_proof.update(native_axis_primitive=ap,source_sketch=axis_sketch,source_sketch_frame_provenance=axis_frame)
            dependency_ids.append(axis_sketch['object_id'])
        else:
            _,native_axis=typed(entity['object_id'],NATIVE_AXIS)
            axis_attributes,axis_cursor=attributes(native_axis,2)
            axis_values=numbers(native_axis,axis_cursor,6);axis_length=math.hypot(*axis_values[3:])
            if (native_axis[:2]!=b'\0\1' or axis_attributes!={'EntityGenesis':0}
                    or len(native_axis) not in (186,244) or any(not math.isfinite(v) for v in axis_values)
                    or not math.isfinite(axis_length) or axis_length<=TOL
                    or math.dist(axis_values[:3],entity['origin_cm'])>TOL
                    or math.dist([v/axis_length for v in axis_values[3:]],entity['direction'])>TOL):
                raise ValueError('Revolve source typed native axis coefficients and selected entity differ')
            axis_proof['native_axis_coefficients']=dict(raw_origin_cm=axis_values[:3],raw_direction=axis_values[3:],
                normalized_direction=[v/axis_length for v in axis_values[3:]])
            if 'origin_container_object_id' in entity:
                container_id=entity['origin_container_object_id'];_,container=typed(container_id,'2972A3B8-3627-49BC-8C3D-18707605EC44')
                if (len(container)!=96 or container[:8]!=bytes(4)+struct.pack('<I',7)
                        or len({reference(container,8+11*i) for i in range(7)})!=7
                        or [reference(container,8+11*i) for i in range(7)].count(entity['object_id'])!=1
                        or reference(container,85)!=component or reference(native_axis,len(native_axis)-11)!=container_id):
                    raise ValueError('Revolve source native origin-axis/container/component differs')
                support(reference(desc,240),[descriptor_id],descriptor_id)
                axis_proof.update(origin_container_object_id=container_id,native_origin_container=raw(container_id))
            else:
                owner=entity['feature_object_id'];defs=[d for d in axis_definitions['definitions'] if d['feature_object_id']==owner]
                if len(defs)!=1 or defs[0]['definition_kind']!='TwoPoints':raise ValueError('Revolve source custom axis requires explicit TwoPoints definition')
                definition=defs[0];positions=[s['entity']['component_position_cm'] for s in definition['support_inputs']]
                delta=[b-a for a,b in zip(*positions)];length=math.hypot(*delta)
                if (not math.isfinite(length) or length<=TOL or math.dist(positions[0],entity['origin_cm'])>TOL
                        or math.dist([v/length for v in delta],entity['direction'])>TOL):
                    raise ValueError('Revolve source custom axis native defining points/cache coefficients differ')
                defining_points=[]
                for s in definition['support_inputs']:
                    ss=[f for f in private if f['kind']=='Sketch' and f['sketch_object_id']==s['entity']['sketch_object_id']]
                    if len(ss)!=1 or frame(ss[0])['component_object_id']!=component:raise ValueError('Revolve source custom-axis support Sketch frame differs')
                    point_id=s['entity']['geometry_object_id'];_,point_bytes=typed(point_id,POINT)
                    pp,pc=attributes(point_bytes,2);local_position=numbers(point_bytes,pc+19,3)
                    if (point_bytes[:2]!=b'\0\1' or len(point_bytes)-pc!=99
                            or pp.get('pt_tag')!=s['entity']['entity_tag']
                            or reference(point_bytes,len(point_bytes)-11)!=ss[0]['sketch_object_id']
                            or any(not math.isfinite(v) for v in local_position)
                            or math.dist(transform_point(ss[0]['placement']['sketch_to_component_matrix'],local_position),s['entity']['component_position_cm'])>TOL):
                        raise ValueError('Revolve source custom-axis defining native POINT differs')
                    defining_points.append(dict(native_point=raw(point_id),native_sketch_frame=frame(ss[0]),
                        local_position_cm=local_position,component_position_cm=s['entity']['component_position_cm']))
                    dependency_ids.append(ss[0]['object_id'])
                collection_id=reference(native_axis,len(native_axis)-11);_,collection=typed(collection_id,'A8635B5F-1E2C-45FD-8BA9-0173B0FEB75E')
                if (len(collection)!=73 or struct.unpack_from('<I',collection,2)[0]!=1 or reference(collection,6)!=entity['object_id']
                        or struct.unpack_from('<I',collection,47)[0]!=1 or reference(collection,51)!=entity['object_id'] or reference(collection,62)!=component):
                    raise ValueError('Revolve source custom-axis repeated collection/component differs')
                support(reference(desc,240),[owner,descriptor_id],descriptor_id);dependency_ids.append(owner)
                axis_proof.update(construction_definition=definition,native_defining_points=defining_points,native_axis_collection=raw(collection_id),
                    independently_derived_axis=dict(origin_cm=positions[0],direction=[v/length for v in delta]))
            axis_proof['native_records'].append(raw(entity['object_id']))
    elif entity['kind']=='BRepEdge':
        descriptor_id=descriptor_ids[0];typed(descriptor_id,'5662F619-2281-4AD9-93DC-1FCFDA1062E7')
        incidence=decode_selection_recipe_incidence(data,records,private,member,members,mappings,descriptor_ids=[descriptor_id])
        rows=[r for r in incidence['associations'] if r['descriptor_object_id']==descriptor_id and r['owner_object_id']==receiver]
        if len(rows)!=1:raise ValueError('Revolve source BRep axis exact name/reciprocal incidence unresolved')
        proof=rows[0];cached=proof['cached_source']
        if (proof['native_body_object_id']!=entity['native_body_object_id'] or proof['body_anchor_object_id']!=entity['body_anchor_object_id']
                or cached['kind']!='Edge' or cached['geometry']['kind']!='Line'
                or math.dist(cached['raw_endpoint_points'][0],entity['start_cm'])>TOL
                or math.dist(cached['raw_endpoint_points'][1],entity['end_cm'])>TOL):
            raise ValueError('Revolve source identity-qualified BRep EDGE and explicit axis context disagree')
        origin=cached['geometry']['raw_origin'];direction=cached['geometry']['direction'];domain=cached['parameter_domain']
        if (len(domain)!=2 or any(not math.isfinite(v) for v in origin+direction+domain) or domain[1]<=domain[0]
                or math.hypot(*direction)<=TOL):
            raise ValueError('Revolve source exact selected EDGE Line coefficients/domain are nonfinite or degenerate')
        line_evaluations=[[o+t*d for o,d in zip(origin,direction)] for t in domain]
        residuals=[math.dist(p,q) for p,q in zip(line_evaluations,cached['raw_endpoint_points'])]
        if any(not math.isfinite(v) or v>TOL for v in residuals):
            raise ValueError('Revolve source exact selected EDGE Line/domain and native endpoint POINTs disagree')
        axis_proof.update(source_line_coefficient_corroboration=dict(raw_origin=origin,direction=direction,parameter_domain=domain,
            endpoint_evaluations_cm=line_evaluations,endpoint_residuals_cm=residuals),source_recipe_incidence=proof,source_geometry_scope='Explicit source EDGE naming/incidence identity precedes cached Line-context coefficient corroboration; not target-cache fitting')
        axis_proof['native_records'] += [raw(descriptor_id),raw(proof['recipe_object_id']),raw(proof['context_object_id']),raw(proof['body_anchor_object_id'])]
        dependency_ids.append(proof['historical_source_owner_object_id']);body_ids.append(proof['native_body_object_id'])
    else:raise ValueError('Revolve source selected axis kind outside captured family')
    axis_origin=entity['origin_cm'];axis_direction=entity['direction']
    if (any(not math.isfinite(v) for v in axis_origin+axis_direction) or not math.isclose(math.hypot(*axis_direction),1.,abs_tol=TOL)):
        raise ValueError('Revolve source native selected axis coefficients nonfinite/nonunit')
    ownership=[]
    for bid in dict.fromkeys(body_ids):
        rows=[p for p in properties['bodies'] if p['object_id']==bid]
        if len(rows)!=1 or rows[0].get('component_object_id')!=component or 'collection_object_id' not in rows[0]:
            raise ValueError('Revolve source native BODY/axis/profile component ownership differs')
        prop=rows[0];cid=prop['collection_object_id'];cs=[c for c in properties['collections'] if c['object_id']==cid]
        _,cb=typed(cid,COLLECTION);_,bb=typed(bid,BODY)
        if len(cs)!=1 or bid not in cs[0]['body_object_ids'] or reference(bb,len(bb)-11)!=cid or reference(cb,len(cb)-11)!=component:
            raise ValueError('Revolve source BODY/repeated collection/component backlinks differ')
        ownership.append(dict(native_body_object_id=bid,body_properties=prop,collection=cs[0]))
    dependencies=[dict(object_id=i) for i in dict.fromkeys(dependency_ids)];decode_dependencies(data,records,dependencies,assembly)
    if any(f.get('component_object_id')!=component or 'component_scope_object_id' not in f for f in dependencies):
        raise ValueError('Revolve source fresh receiving/profile/axis dependency components differ')
    group=dict(source_feature_object_id=receiver,native_body_object_id=native,body_anchor_object_id=anchor_id,source_anchor=anchor,
        binding=binding,mapping_record_object_id=mapping['mapping_record_object_id'],history_blob_member=mapping['history_blob_member'],
        asm_body_index=binding['asm_body_index'],native_profile_kind=family,source_sketch=sketch,
        source_sketch_frame_provenance=profile_frame,native_profile_selection=dict(profile_descriptor_object_id=descriptor.object_id,
            profile_loop_definition_object_id=definition_id,native_sketch_object_id=sketch_id,namespace_text=namespace,
            profile_loops=loops,descriptor_native_record=raw(descriptor.object_id),loop_native_record=raw(definition_id)),
        profile_primitives=primitives,native_profile_points=list(points.values()),profile_point_cycle=point_cycle,profile_line_cycle=line_cycle,
        profile_cycle_scope='Source-only mathematical endpoint positions join into abstract roles; native POINT IDs and Line endpoint pairs remain distinct, no native welding/vertex identity is inferred',
        native_POINT_welding=None,
        mathematical_profile=mathematical_profile,mathematical_inputs=dict(profile=mathematical_profile,
            sketch_to_component_matrix=matrix,source_axis=dict(origin_cm=axis_origin,direction=axis_direction),controls=controls))
    if mathematical_profile['kind']=='Polygon':
        group['mathematical_endpoint_roles']=[dict(source_primitive_id=i,endpoint_roles=pair,native_POINT_ids=next(p['native_point_object_ids'] for p in primitives if p['source_primitive_id']==i)) for i,pair in endpoint_roles.items()]
        group['mathematical_vertex_native_POINT_observations']=[dict(mathematical_role=i,position_cm=mathematical_vertices[i],native_POINT_ids=list(dict.fromkeys(role_points[i]))) for i in range(len(mathematical_vertices))]
    return dict(feature_object_id=receiver,original_controls=controls,source_axis=axis,source_axis_provenance=axis_proof,
        source_groups=[group],source_group_count=1,component_provenance=dict(component_object_id=component,body_ownership=ownership,
            dependency_scopes=dependencies,assembly_scope=assembly['scope']),feature_native_record=raw(receiver),
        effective_axis=None,exact_API_handle_identity=None,persistent_identity=None,qualified_historical_state=None,
        cache_lifecycle_scope='Explicit creator-owned BODY and same-asset stored-ID association only; no before/current/final state',scope=SCOPE)
