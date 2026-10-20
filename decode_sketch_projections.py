"""Observed explicit sketch projection/inclusion provenance and output caches."""

import math
import struct

from decode_brep_recipes import RECIPE_GUID, decode_recipe
from decode_selection import native_proxy_references
from decode_sketch import ascii_string, attributes, numbers, reference, same


CONTROLLER_GUID = "F1451EC8-11A4-4952-84ED-5AB7C13E2E83"
ENTRY_GUID = "CA72DD8E-2861-4DDD-9721-03039B5FB113"
CURVE_SOURCE_GUID = "E2CEFD18-D755-4E09-8E7F-953A2F6D43F8"
POINT_SOURCE_GUID = "D95DBAC0-238B-4429-A0AD-4AE5BEE79ADF"
NAME_GUIDS = ("CB4F4CC2-9D6F-48BA-9B1F-20C1992C9C9C", "4B31DA1B-FCD6-4527-BC3E-BE1FBAF867FE")


def decode_sketch_projections(data, records, features):
    sketches = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
    by_feature = {f["object_id"]: f for f in sketches.values()}
    decoded, unresolved = [], []

    def primary(identity, guid=None):
        candidates = [r for r in records if r.is_primary and r.object_id == identity
                      and (guid is None or r.class_guid == guid)]
        if len(candidates) != 1:
            raise ValueError("Projection typed reference missing or ambiguous")
        record = candidates[0]
        return record, data[record.body:record.end]

    def source_leaf(record, payload):
        if record.class_guid == CURVE_SOURCE_GUID and len(payload) == 26 and payload[:10] == b"\0"*10:
            sketch_id, tag = struct.unpack_from("<QQ", payload, 10)
            allowed = ("Line", "Circle")
        elif record.class_guid == POINT_SOURCE_GUID and len(payload) == 18 and payload[:2] == b"\0\0":
            sketch_id, tag = struct.unpack_from("<QQ", payload, 2)
            allowed = ("Point",)
        else:
            raise ValueError("Unsupported projection source leaf")
        sketch = sketches.get(sketch_id)
        if sketch is None:
            raise ValueError("Projection source sketch unresolved")
        matches = [g for g in sketch.get("geometry", []) if g.get("entity_tag") == tag and g["kind"] in allowed]
        if len(matches) != 1:
            raise ValueError("Projection source sketch entity/tag unresolved or ambiguous")
        return {"kind": "SketchEntity", "source_leaf_object_id": record.object_id,
                "sketch_object_id": sketch_id, "sketch_name": sketch["name"],
                "entity_tag": tag, "entity_object_id": matches[0]["object_id"], "entity_kind": matches[0]["kind"]}

    def naming_leaf(identity):
        record, payload = primary(identity)
        if record.class_guid not in NAME_GUIDS or payload[:1] != b"\0" or payload[1] not in (0, 1):
            raise ValueError("Unsupported projected-output naming record")
        cursor, links = 2, {}
        if payload[1]:
            count = struct.unpack_from("<I", payload, cursor)[0]
            cursor += 4
            if count > 2:
                raise ValueError("Unsupported projection progenitor attribute count")
            for _ in range(count):
                name, cursor = ascii_string(payload, cursor)
                kind, cursor = ascii_string(payload, cursor)
                if name in links or name not in ("EdgeEndVertexProgenitor", "EdgeStartVertexProgenitor") or kind != "StrongRefMetaType":
                    raise ValueError("Unsupported projection progenitor attribute")
                links[name] = reference(payload, cursor)
                primary(links[name])
                cursor += 11
        if len(payload) != cursor+12 or payload[-1] != 0:
            raise ValueError("Unsupported projection naming-record suffix")
        leaf_id = reference(payload, cursor)
        leaf_record, leaf_payload = primary(leaf_id)
        return record.object_id, leaf_record, leaf_payload, links

    def cached_output(record, payload, target_sketch_id):
        if payload[:2] != b"\0\1" or reference(payload, len(payload)-11) != target_sketch_id:
            raise ValueError("Projection output cache owner disagrees with target sketch")
        props, cursor = attributes(payload, 2)
        if props.get("EntityGenesis") != 0:
            raise ValueError("Unobserved projected-output genesis")
        result = {"object_id": record.object_id, "sketch_object_id": target_sketch_id,
                  "entity_genesis": props["EntityGenesis"], "coordinate_system": "sketch-local", "coordinate_units": "cm"}

        def point(identity):
            point_record, chunk = primary(identity, "C2CEDAE7-1716-47C1-B7B1-07B70081D0FB")
            point_props, start = attributes(chunk, 2)
            if chunk[:2] != b"\0\1" or len(chunk)-start != 99 or reference(chunk, len(chunk)-11) != target_sketch_id:
                raise ValueError("Projection cache endpoint owner/layout disagrees")
            return numbers(chunk, start+19, 3)

        if record.class_guid in ("DCA267ED-D615-4934-B64F-AD805E8003E2", "F0130424-8B7E-4092-93C9-1CA807482534") and props.get("crv_secondary_id") != 0:
            raise ValueError("Unsupported projected secondary curve representation")
        if record.class_guid == "DCA267ED-D615-4934-B64F-AD805E8003E2" and len(payload)-cursor == 171:
            values = numbers(payload, cursor, 12)
            end_id, start_id = reference(payload, cursor+96), reference(payload, cursor+107)
            start, end = point(start_id), point(end_id)
            if not same(values[:3], start) or not same([a+b for a, b in zip(values[:3], values[3:6])], end):
                raise ValueError("Projection line cache endpoints disagree")
            result.update(kind="Line", entity_tag=props["crv_primary_id"], start_point_id=start_id,
                          end_point_id=end_id, start_cm=start, end_cm=end)
        elif record.class_guid == "F0130424-8B7E-4092-93C9-1CA807482534" and len(payload)-cursor == 162:
            values = numbers(payload, cursor, 12)
            center_id = reference(payload, cursor+96)
            if (not same(values[:3], point(center_id)) or values[9] <= 0 or not same(values[10:], [0, 2*math.pi])
                    or not same([sum(v*v for v in values[3:6]), sum(v*v for v in values[6:9]),
                                 sum(a*b for a, b in zip(values[3:6], values[6:9]))], [1, 1, 0])):
                raise ValueError("Unsupported projected circle cache")
            result.update(kind="Circle", entity_tag=props["crv_primary_id"], center_point_id=center_id,
                          center_cm=values[:3], normal=values[3:6], reference_axis=values[6:9], radius_cm=values[9])
        elif record.class_guid == "C2CEDAE7-1716-47C1-B7B1-07B70081D0FB" and len(payload)-cursor == 99:
            result.update(kind="Point", entity_tag=props["pt_tag"], position_cm=numbers(payload, cursor+19, 3))
        else:
            raise ValueError("Unsupported projected output cache geometry")
        return result

    for controller in records:
        if not controller.is_primary or controller.class_guid != CONTROLLER_GUID:
            continue
        try:
            chunk = data[controller.body:controller.end]
            if len(chunk) != 105 or chunk[:5] != bytes.fromhex("0000010000") or chunk[5] not in (0, 1):
                raise ValueError("Unsupported projection controller layout")
            owner = reference(chunk, 94)
            target_sketch = by_feature.get(owner)
            if target_sketch is None or reference(chunk, 30) != owner:
                raise ValueError("Projection controller target sketch owner unresolved")
            entry_id, proxy_id = reference(chunk, 6), reference(chunk, 41)
            _, entry = primary(entry_id, ENTRY_GUID)
            if len(entry) != 33 or entry[:6] != bytes.fromhex("000001000000") or struct.unpack_from("<Q", entry, 25)[0] != 1:
                raise ValueError("Unsupported projection output entry")
            output_id = struct.unpack_from("<Q", entry, 17)[0]
            output_record, output_payload = primary(output_id)
            naming_id, named_leaf, named_payload, endpoint_progenitors = naming_leaf(reference(entry, 6))
            proxy, proxy_payload = primary(proxy_id, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
            if reference(proxy_payload, len(proxy_payload)-11) != owner:
                raise ValueError("Projection source proxy owner disagrees")
            descriptors, props = native_proxy_references(data, proxy)
            if props or len(descriptors) != 1:
                raise ValueError("Unsupported projection source descriptor count/attributes")
            descriptor, descriptor_payload = primary(descriptors[0])
            if reference(descriptor_payload, len(descriptor_payload)-11) != owner:
                raise ValueError("Projection source descriptor owner disagrees")
            if descriptor.class_guid == "5A1BF548-241F-46FD-9FB5-E4B05126EB9D" and len(descriptor_payload) == 263 and descriptor_payload[:2] == b"\0\0":
                proxy_leaf, proxy_leaf_payload = primary(reference(descriptor_payload, 2))
                source = source_leaf(proxy_leaf, proxy_leaf_payload)
                named_source = source_leaf(named_leaf, named_payload)
                if any(source[key] != named_source[key] for key in ("sketch_object_id", "entity_tag", "entity_kind")):
                    raise ValueError("Projection input proxy and output naming source disagree")
                source["output_naming_source_leaf_object_id"] = named_leaf.object_id
            elif (descriptor.class_guid == "5662F619-2281-4AD9-93DC-1FCFDA1062E7"
                  and len(descriptor_payload) == 276 and descriptor_payload[:4] == bytes.fromhex("00000001")):
                proxy_leaf, _ = primary(reference(descriptor_payload, 4), RECIPE_GUID)
                if named_leaf.class_guid != RECIPE_GUID:
                    raise ValueError("Projection body-edge output naming recipe class disagrees")
                input_recipe = decode_recipe(data, proxy_leaf)
                output_recipe = decode_recipe(data, named_leaf)
                if input_recipe["payload_kind"] != "edge_recipe_data" or output_recipe["payload_kind"] != "edge_recipe_data":
                    raise ValueError("Unsupported projected BRep recipe kind")
                if input_recipe["name_table"] != output_recipe["name_table"]:
                    raise ValueError("Projection input/output recipe name tables disagree")
                source = {"kind": "BRepEdgeRecipe", "input_recipe": input_recipe, "output_naming_recipe": output_recipe,
                          "topology_status": "Explicit native edge recipes retained; persistent BRep/ASM edge identity unresolved"}
            else:
                raise ValueError("Unsupported projection source descriptor variant")
            output = cached_output(output_record, output_payload, target_sketch["sketch_object_id"])
            decoded.append({"controller_object_id": controller.object_id, "entry_object_id": entry_id,
                            "target_feature_object_id": owner, "target_sketch_object_id": target_sketch["sketch_object_id"],
                            "target_sketch_name": target_sketch["name"], "method": "Project" if chunk[5] else "Include",
                            "stored_projection_mode": chunk[5], "is_linked": True,
                            "source_proxy_object_id": proxy_id, "source_descriptor_object_id": descriptor.object_id,
                            "output_naming_record_object_id": naming_id, "endpoint_progenitor_record_object_ids": endpoint_progenitors,
                            "source": source, "output_cache": output,
                            "link_status": "Explicit controller/output-entry/source-proxy and output naming references"})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({"object_id": controller.object_id, "reason": str(error)})
    return {"relationships": decoded, "unresolved": unresolved,
            "scope": "Observed linked Project/Include provenance with explicit output geometry caches; missing controllers do not prove geometry was never linked",
            "limitations": "Multiple outputs, silhouette/cut/intersection, transformed occurrences, general projected conics/splines and persistent BRep topology unresolved"}
