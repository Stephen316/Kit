"""Observed simple surface-tool controls; regeneration remains unsupported."""

import struct

from decode_selection import native_proxy_references
from decode_sketch import reference


def decode_surface_tool(data, records, body, feature):
    classes = {"SurfacePatch": "BF77AE1A-E8F6-43AB-A325-A2C984AF1C6B",
               "SurfaceOffset": "1589BC73-D484-4A6E-8E69-2A1531E845F5",
               "SurfaceStitch": "16722593-7399-4963-9EB3-656FE1949577",
               "Unstitch": "8DA2F4A9-C420-419B-AD5D-9CC901DF0B78",
               "ReverseNormal": "693D6578-4BCE-44F8-B15A-2CE5162A23EE",
               "SurfaceDeleteFace": "2C122D9F-4F8A-6383-D14C-E00CE77B2226"}
    kind = feature["kind"]
    if feature["class_guid"] != classes[kind]:
        raise ValueError("Unrecognized surface-tool class")

    def primary(identity, guid=None):
        matches = [r for r in records if r.is_primary and r.object_id == identity
                   and (guid is None or r.class_guid == guid)]
        if len(matches) != 1:
            raise ValueError("Surface-tool typed reference missing or ambiguous")
        return matches[0]

    def selection(identity):
        record = primary(identity, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
        chunk = data[record.body:record.end]
        if reference(chunk, len(chunk)-11) != feature["object_id"]:
            raise ValueError("Surface-tool proxy owner disagrees with feature")
        descriptors, props = native_proxy_references(data, record)
        for descriptor_id in descriptors:
            descriptor = primary(descriptor_id)
            payload = data[descriptor.body:descriptor.end]
            if reference(payload, len(payload)-11) != feature["object_id"]:
                raise ValueError("Surface-tool descriptor owner disagrees with feature")
        return {"selection_record_object_id": identity, "descriptor_object_ids": descriptors,
                "stored_descriptor_count": len(descriptors)}, props

    def parameter(identity, role):
        matches = [p for p in feature["parameters"] if p["binding_object_id"] == identity and p["role"] == role]
        if len(matches) != 1:
            raise ValueError("Surface-tool parameter binding unresolved: "+role)
        return matches[0]["raw_float64"]

    def counted_refs(cursor, expected_count=None, guid=None):
        count = struct.unpack_from("<I", body, cursor)[0]
        if not 0 <= count <= 1024 or (expected_count is not None and count != expected_count):
            raise ValueError("Unsupported surface-tool reference count")
        identities = [reference(body, cursor+4+11*i) for i in range(count)]
        for identity in identities:
            primary(identity, guid)
        return identities, cursor+4+11*count

    result = {"input_selection_status": "Explicit proxy/descriptor ownership; general persistent topology mapping unresolved"}
    if kind == "SurfacePatch":
        if (body[:13] != bytes.fromhex("00010000000000000000000100")
                or struct.unpack_from("<I", body, 13)[0] != 4 or body[17:21] != b"\0"*4):
            raise ValueError("Unsupported basic sketch-profile patch layout")
        proxies, _ = counted_refs(21, 1)
        selected, _ = selection(proxies[0])
        profiles = feature.get("profile_selection", [])
        if len(profiles) != 1 or selected["descriptor_object_ids"] != [profiles[0]["descriptor_object_id"]]:
            raise ValueError("Patch profile descriptor/curve membership unresolved")
        result.update(operation="NewBody", boundary_selection=selected,
                      boundary_curve_count=sum(len(loop["curve_references"]) for loop in profiles[0]["loops"]),
                      continuity_status="Only default sketch-profile patch observed; continuity/group fields unverified")
    elif kind == "SurfaceOffset":
        if body[:6] != bytes.fromhex("000100000000") or body[6] not in (0, 1) or body[7] not in (0, 1):
            raise ValueError("Unsupported surface offset prefix")
        if body[19:23] != b"\0"*4 or body[38:42] != b"\0"*4:
            raise ValueError("Unsupported surface offset result/selection fields")
        outputs, _ = counted_refs(23, 1, "D26351F0-5940-4D23-AA20-2C35475A6D9E")
        proxies, _ = counted_refs(42, 1)
        selected, _ = selection(proxies[0])
        binding = reference(body, 8)
        result.update(distance_cm=parameter(binding, "offset"), distance_binding_object_id=binding,
                      is_chain_selection=bool(body[7]), offset_type={0: "Sharp", 1: "Rounded"}[body[6]],
                      stored_offset_type_code=body[6], selection=selected,
                      result_record_object_ids=outputs, operation_status="Native operation field not decoded")
    elif kind == "SurfaceStitch":
        if body[:6] != bytes.fromhex("000100000000") or struct.unpack_from("<I", body, 6)[0] != 4:
            raise ValueError("Unsupported observed stitch prefix/operation")
        proxies, cursor = counted_refs(49, 2)
        selected = [selection(identity) for identity in proxies]
        operation_flag = struct.unpack_from("<Q", body, 30)[0]
        if any(props.get("DcFeatureOperationIdFlag") != operation_flag for _, props in selected):
            raise ValueError("Stitch operation flag copies disagree")
        binding = reference(body, cursor)
        result.update(tolerance_cm=parameter(binding, "StitchingTolerence"), tolerance_binding_object_id=binding,
                      selections=[item for item, _ in selected], stored_operation_code=4,
                      stored_operation_flag=operation_flag,
                      operation_status="Stored operation retained; API operation is ignored for the observed open-sheet result")
    elif kind == "Unstitch":
        if body[:6] != bytes.fromhex("000100000000") or body[6] not in (0, 1) or body[7:11] != b"\0"*4:
            raise ValueError("Unsupported unstitch prefix")
        outputs, cursor = counted_refs(11, guid="D26351F0-5940-4D23-AA20-2C35475A6D9E")
        auxiliary, cursor = counted_refs(cursor, 1 if body[6] else 0, "D26351F0-5940-4D23-AA20-2C35475A6D9E")
        proxies, _ = counted_refs(cursor, 1)
        selected, _ = selection(proxies[0])
        result.update(is_chain_selection=bool(body[6]), expanded_selection=selected,
                      result_record_object_ids=outputs, auxiliary_record_object_ids=auxiliary,
                      expansion_status="Stored chain selection can expand one API input into several face descriptors; original input count not inferred")
    else:
        cursor = 2 if kind == "ReverseNormal" else 14
        if body[:cursor] != b"\0"*cursor:
            raise ValueError("Unsupported surface deletion/reversal prefix")
        proxies, _ = counted_refs(cursor, 1)
        selected, _ = selection(proxies[0])
        result.update(selection=selected,
                      mode_status="Observed surface-normal reversal" if kind == "ReverseNormal" else
                                  "Observed surface deletion leaving an opening; no general healing controls decoded")
    return result
