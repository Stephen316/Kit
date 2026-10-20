"""Observed planar sketch surface constraints and their explicit source chains.

No solver, general 3D curve support, assembly context or persistent face identity.
The standalone reader never mutates caller features or existing reader defaults.
"""

import math
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import RECIPE_GUID, decode_recipe
from decode_parameters import read_string
from decode_placement import cross
from decode_selection import known_construction_entities, native_proxy_references
from decode_sketch import attributes, constraint_prefix, numbers, reference, same

CONSTRAINT = "60403D47-0C49-49B0-BDE8-1679608164A2"
PLANE_CACHE = "6F542DE3-39A5-47D6-A55B-4AD354B879F1"
CONTROLLER = "312A88A1-FAFE-40E8-9778-962FC7DC0ACC"
ENTRY = "CA72DD8E-2861-4DDD-9721-03039B5FB113"
PROXY = "2CA5A1CD-C99B-4C9B-91AF-57989148E841"
NATIVE_LEAF = "90055C05-546C-4EE7-B3C9-3DD922AD0C9C"
METHODS = {1: ("CoincidentToSurface", "Point", "point", "surface"),
           2: ("LineOnPlanarSurface", "Line", "line", "planarSurface"),
           16: ("LineParallelToPlanarSurface", "Line", "line", "planarSurface"),
           32: ("PerpendicularToSurface", "Line", "curve", "surface")}


SCOPE = 'Observed Point/Line planar CoincidentToSurface, LineOnPlanarSurface, LineParallelToPlanarSurface and PerpendicularToSurface with explicit source chains'
LIMITATIONS = 'No general 3D/curved surfaces, transformed occurrence contexts, solver regeneration, style semantics or persistent BRep face mapping'

def decode_sketch_surface_constraints(data, records, features):
    """Return constraints/additional_geometry/relationships/unresolved; no mutation.

    Call after decode_sketches; geometry and source IDs come from explicit native
    links. Successful IDs alone may be used to account sketch record coverage.
    """
    grouped = {}
    for r in records:
        if r.is_primary:
            grouped.setdefault(r.object_id, []).append(r)
    primary = {i: rs[0] for i, rs in grouped.items() if len(rs) == 1}
    if not any(r.class_guid == PLANE_CACHE for r in primary.values()):
        return {"constraints":[],"additional_geometry":[],"relationships":[],"unresolved":[],
                "scope":SCOPE,"limitations":LIMITATIONS}
    sketches = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
    geometry = {g["object_id"]: g for s in sketches.values() for g in s.get("geometry", [])}
    known = known_construction_entities(data, records, features)
    anchors = {a["object_id"]: a for a in decode_body_selections(data, records)["body_anchors"]}
    constraints, planes, relationships, unresolved = [], {}, {}, []

    def typed(identity, guid=None):
        r = primary.get(identity)
        if r is None or (guid is not None and r.class_guid != guid):
            raise ValueError("Surface constraint typed reference missing/ambiguous: " + str(identity))
        return r, data[r.body:r.end]

    def native_leaf(identity):
        _, b = typed(identity, NATIVE_LEAF)
        if len(b) != 10 or b[:2] != b"\0\0":
            raise ValueError("Unsupported native construction-plane leaf")
        native_id = struct.unpack_from("<Q", b, 2)[0]
        entity = known.get(native_id)
        if entity is None or entity["kind"] != "ConstructionPlane":
            raise ValueError("Surface source native construction plane unresolved")
        typed(native_id, "8D424E29-DE23-4B1F-A3AD-84C52A497D1A")
        return native_id, entity

    def source_for(cache_id, sketch):
        candidates = []
        for root in primary.values():
            if root.class_guid != CONTROLLER:
                continue
            b = data[root.body:root.end]
            if len(b) != 89 or b[:2] != b"\0\0":
                continue
            try:
                entry_id = reference(b, 2)
                _, e = typed(entry_id, ENTRY)
                if len(e) != 33 or e[:6] != bytes.fromhex("000001000000") or struct.unpack_from("<Q",e,25)[0] != 1:
                    continue
                if struct.unpack_from("<Q", e, 17)[0] == cache_id:
                    candidates.append((root, b, entry_id, e))
            except (ValueError,struct.error):
                continue
        if len(candidates) != 1:
            raise ValueError("Surface cache has no unique explicit controller/output entry")
        root, b, entry_id, e = candidates[0]
        owner = sketch["object_id"]
        if reference(b,13) != owner or reference(b,78) != owner or b[24] != 1:
            raise ValueError("Surface controller target feature ownership disagrees")
        proxy_id = reference(b,25)
        proxy,p = typed(proxy_id,PROXY)
        ds,props = native_proxy_references(data,proxy)
        if len(p) != 105 or reference(p,len(p)-11) != owner or props or len(ds) != 1:
            raise ValueError("Unsupported surface proxy count/owner/attributes")
        descriptor,d = typed(ds[0])
        if reference(d,len(d)-11) != owner:
            raise ValueError("Surface descriptor owner disagrees")
        naming_id = reference(e,6)
        naming,n = typed(naming_id)
        if len(n) != 18 or n[:6] != bytes.fromhex("000100000000") or n[-1] != 0:
            raise ValueError("Unsupported surface output naming layout")
        named_leaf_id = reference(n,6)
        result = {"controller_object_id":root.object_id,"entry_object_id":entry_id,
                  "target_feature_object_id":owner,"target_sketch_object_id":sketch["sketch_object_id"],
                  "source_proxy_object_id":proxy_id,"source_descriptor_object_id":descriptor.object_id,
                  "output_naming_record_object_id":naming_id,"output_naming_leaf_object_id":named_leaf_id,
                  "output_cache_object_id":cache_id,
                  "uninterpreted_controller_middle_hex":b[36:78].hex()}
        if descriptor.class_guid == "5A1BF548-241F-46FD-9FB5-E4B05126EB9D":
            if len(d) != 263 or d[:2] != b"\0\0" or struct.unpack_from("<I",d,13)[0] != 1:
                raise ValueError("Unsupported surface construction-plane descriptor")
            namespace,c = read_string(d,17); entity_uuid,c = read_string(d,c)
            if c != 169 or struct.unpack_from("<QI",d,c) != (2,1):
                raise ValueError("Unsupported construction-plane descriptor context framing")
            _,frame = typed(reference(d,181),"CC54ECAD-6DE8-4DE1-803D-BBE0E751975B")
            source_leaf_id = reference(d,2)
            native_id,entity = native_leaf(source_leaf_id)
            output_id,_ = native_leaf(named_leaf_id)
            _,context_name = typed(reference(frame,len(frame)-11),"CB4F4CC2-9D6F-48BA-9B1F-20C1992C9C9C")
            if len(context_name) != 14 or context_name[:2] != b"\0\0" or context_name[-1] != 0:
                raise ValueError("Unsupported construction-plane context naming")
            context_native_id,_ = native_leaf(reference(context_name,2))
            if context_native_id != native_id:
                raise ValueError("Surface context/input native plane naming disagrees")
            if naming.class_guid != "CB4F4CC2-9D6F-48BA-9B1F-20C1992C9C9C" or output_id != native_id:
                raise ValueError("Surface input/output native plane naming disagrees")
            source = {"kind":"ConstructionPlane","source_leaf_object_id":source_leaf_id,
                      "native_plane_object_id":native_id,"entity":entity,
                      "context_object_id":reference(d,181),"uninterpreted_descriptor_trailer_hex":d[192:252].hex()}
        elif descriptor.class_guid == "5662F619-2281-4AD9-93DC-1FCFDA1062E7":
            if len(d) != 276 or d[:4] != b"\0"*4 or struct.unpack_from("<I",d,15)[0] != 1:
                raise ValueError("Unsupported surface face descriptor")
            namespace,c = read_string(d,19); entity_uuid,c = read_string(d,c)
            if c != 171 or struct.unpack_from("<QI",d,c) != (2,1):
                raise ValueError("Unsupported face descriptor context framing")
            context = reference(d,183);typed(context,"C46D3EEB-40E1-43FA-83DC-9CB204335417")
            if struct.unpack_from("<I",d,194)[0] != 1:
                raise ValueError("Unsupported surface face body-anchor count")
            anchor_id = reference(d,198)
            if anchor_id not in anchors:
                raise ValueError("Surface face source anchor unresolved")
            input_r,_ = typed(reference(d,4),RECIPE_GUID); output_r,_ = typed(named_leaf_id,RECIPE_GUID)
            input_recipe = decode_recipe(data,input_r,primary); output_recipe = decode_recipe(data,output_r,primary)
            if (naming.class_guid != "4B31DA1B-FCD6-4527-BC3E-BE1FBAF867FE"
                    or input_recipe["payload_kind"] != "bounded_face_recipe_data" or output_recipe["payload_kind"] != "face_recipe_data"):
                raise ValueError("Unsupported surface input/output face recipe kinds")
            input_terms = [t for entry in input_recipe["name_table"] for t in entry["terms"]]
            output_terms = [t for entry in output_recipe["name_table"] for t in entry["terms"]]
            if len(output_terms) != 1 or output_terms[0] not in input_terms or output_terms[0]["stored_reference_tag"] != 1:
                raise ValueError("Surface output face name is not an explicit bounded-input term")
            anchor = anchors[anchor_id]
            source = {"kind":"BRepFaceRecipe","input_recipe":input_recipe,"output_naming_recipe":output_recipe,
                      "body_anchor":anchor,"context_object_id":context,
                      "recipe_stored_numeric_reference_value":output_terms[0]["stored_reference_value"],
                      "uninterpreted_descriptor_trailer_hex":d[209:265].hex(),
                      "topology_status":"Explicit face term and independent source-body anchor retained; recipe numeric body identity and persistent ASM face mapping unresolved"}
        else:
            raise ValueError("Uncaptured surface source descriptor class")
        for value in (namespace,entity_uuid):
            if len(value) != 36:
                raise ValueError("Unsupported surface descriptor UUID length")
            uuid.UUID(value)
        result.update(namespace_text=namespace,entity_guid_text=entity_uuid,source=source)
        return result

    for r in primary.values():
        if r.class_guid != CONSTRAINT:
            continue
        try:
            b = data[r.body:r.end]
            deps,props,c = constraint_prefix(b)
            if not any(primary.get(i) and primary[i].class_guid == PLANE_CACHE for i in deps):
                continue
            if len(deps) != 2 or props != {"EntityGenesis":2} or len(b)-c != 46:
                raise ValueError("Unsupported surface constraint framing")
            if any(b[16+15*i:20+15*i] != b"\0"*4 for i in range(2)):
                raise ValueError("Unobserved surface constraint dependency extras")
            tail=b[c:];owner=reference(tail,0);sketch=sketches.get(owner)
            code,count=struct.unpack_from("<QI",tail,11)
            if sketch is None or code not in METHODS or count != 2 or tail[-1] != 0:
                raise ValueError("Unsupported surface constraint owner/code/arity")
            if deps != [reference(tail,23),reference(tail,34)]:
                raise ValueError("Surface constraint repeated ordered roles disagree")
            kind,member_kind,member_role,surface_role=METHODS[code]
            member=geometry.get(deps[0])
            if member is None or member["kind"] != member_kind or member["sketch_object_id"] != owner:
                raise ValueError("Surface member kind/owner unresolved")
            cache,p=typed(deps[1],PLANE_CACHE);a,start=attributes(p,2)
            if (p[:2] != b"\0\1" or set(a) != {"EntityGenesis","surface_tag"} or a["EntityGenesis"] != 0
                    or len(p)-start != 114 or p[start] != 0 or reference(p,len(p)-11) != owner):
                raise ValueError("Unsupported surface plane cache framing/owner")
            values=numbers(p,start+1,9);origin,x,y=values[:3],values[3:6],values[6:]
            if not same([sum(v*v for v in x),sum(v*v for v in y),sum(a*b for a,b in zip(x,y))],[1,1,0]):
                raise ValueError("Surface plane cache basis is not orthonormal")
            plane={"kind":"SurfacePlane","object_id":cache.object_id,"sketch_object_id":owner,
                   "record_offset":cache.start,"entity_genesis":0,"entity_tag":a["surface_tag"],
                   "coordinate_system":"sketch-local","coordinate_units":"cm","origin_cm":origin,
                   "x_axis":x,"y_axis":y,"normal":cross(x,y),
                   "uninterpreted_style_hex":p[start+73:-11].hex()}
            relation=source_for(cache.object_id,sketch)
            expected_source = "BRepFaceRecipe" if code == 2 else "ConstructionPlane"
            if relation["source"]["kind"] != expected_source:
                raise ValueError("Uncaptured surface method/source-kind combination")
            # Source associations choose IDs; geometric checks only test consistency.
            pts=[member["position_cm"]] if member_kind == "Point" else [member["start_cm"],member["end_cm"]]
            residual=[sum(n*(v-o) for n,v,o in zip(plane["normal"],pt,origin)) for pt in pts]
            if code in (1,2) and any(abs(v)>1e-8 for v in residual):
                raise ValueError("Surface incidence geometry disagrees with relation")
            if member_kind == "Line":
                delta=[b-a for a,b in zip(*pts)];length=math.sqrt(sum(v*v for v in delta))
                if length<=1e-12:
                    raise ValueError("Degenerate constrained surface line")
                dot=sum(a*b for a,b in zip(delta,plane["normal"]))/length
                if (code == 16 and abs(dot)>1e-8) or (code == 32 and abs(abs(dot)-1)>1e-8):
                    raise ValueError("Surface line direction disagrees with relation")
            constraints.append({"object_id":r.object_id,"sketch_object_id":owner,"kind":kind,
                "api_constraint_class":kind+"Constraint","stored_constraint_code":code,
                "entity_ids":deps,"member_role":member_role,"member_object_id":deps[0],
                "surface_role":surface_role,"surface_cache_object_id":deps[1],
                "source_controller_object_id":relation["controller_object_id"],
                "geometry_consistency":{"matches":True,"member_plane_residuals_cm":residual},
                "scope":"Observed Point/Line with planar surface cache; no general 3D curve/solver interpretation"})
            planes[cache.object_id]=plane;relationships[relation["controller_object_id"]]=relation
        except (ValueError,KeyError,IndexError,UnicodeError,struct.error) as error:
            unresolved.append({"object_id":r.object_id,"class_guid":r.class_guid,"reason":str(error)})
    return {"constraints":constraints,"additional_geometry":list(planes.values()),
            "relationships":list(relationships.values()),"unresolved":unresolved,
            "scope":SCOPE,
            "limitations":LIMITATIONS}
