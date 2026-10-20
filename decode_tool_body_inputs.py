"""Link decoded body selections to their explicitly referencing feature records.

Generic ownership is not a target/tool role. Historical selected bodies remain
distinct from later result bodies; no complete feature regeneration is implied.
"""

import re
import struct

from decode_body_selections import DESCRIPTOR, PROXY
from decode_parameters import read_string
from decode_sketch import attributes, reference


def decode_tool_body_inputs(data, records, features, body_selections):
    """Return feature-level groups using reciprocal owners and a bounded table.

    ``body_selections`` may include the populated component-context proxies
    merged by the main decoder. Only their primary descriptor lists are read
    here; component coordinate semantics remain in the original summary.
    """
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in grouped.items() if len(values) == 1}
    descriptors = {item["object_id"]: item for item in body_selections["body_descriptors"]}
    feature_map = {feature["object_id"]: feature for feature in features}
    by_owner, decoded, unresolved = {}, [], []
    for selection in body_selections["selection_proxies"]:
        by_owner.setdefault(selection["owner_object_id"], []).append(selection)

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Feature body input typed reference missing, ambiguous or wrong class")
        return record, data[record.body:record.end]

    def reference_table(payload, feature, required):
        label = feature["native_kind_label"]
        marker = struct.pack("<I", len(label))+label.encode("utf-16le")
        matches = list(re.finditer(re.escape(marker), payload))
        if len(matches) != 1:
            raise ValueError("Feature's native kind label is missing or ambiguous")
        label_position = matches[0].start()
        _, cursor = read_string(payload, label_position)
        if struct.unpack_from("<Q", payload, cursor)[0] != feature["stored_index"]:
            raise ValueError("Native feature index disagrees with named feature")
        # This counted table terminates immediately before the stored metadata
        # flag and native-kind string. References are never found by searching
        # for arbitrary byte patterns inside unrelated feature fields.
        end = label_position-4
        candidates = []
        for count in range(1, min(1024, (end-4)//11)+1):
            start = end-4-11*count
            if struct.unpack_from("<I", payload, start)[0] != count:
                continue
            try:
                identities = [reference(payload, start+4+11*i) for i in range(count)]
            except ValueError:
                continue
            if (len(set(identities)) == count and required.issubset(identities)
                    and all(identity in primary for identity in identities)):
                candidates.append((start, identities))
        if len(candidates) != 1:
            raise ValueError("Unique counted feature table containing its body proxies/descriptors was not established")
        start, identities = candidates[0]
        return {"relative_offset": start, "count": len(identities), "object_ids": identities,
                "stored_metadata_flag": struct.unpack_from("<I", payload, end)[0],
                "association": "Exact counted reference table anchored before this feature's native-kind label"}

    def explicit_role(feature, selected):
        settings = feature.get("tool_settings", {})
        ids = selected["descriptor_object_ids"]
        if feature["kind"] in ("PathPattern", "CircularPattern", "RectangularPattern"):
            expected = [item["descriptor_object_id"] for item in settings.get("input_descriptors", [])]
            if expected and ids == expected and settings.get("input_body_count") == len(ids):
                return "PatternInputBody", "Decoded explicit pattern input-descriptor collection agrees with the body proxy list"
        if feature["kind"] == "Combine":
            matches = [item for item in settings.get("input_selections", [])
                       if item["selection_record_object_id"] == selected["selection_record_object_id"]]
            if (len(matches) == 1 and ids == [matches[0]["descriptor_object_id"]]
                    and matches[0]["role"] in ("TargetBody", "ToolBody")):
                return matches[0]["role"], "Decoded explicit Combine target/tool list agrees with the body proxy and descriptor"
        if feature["kind"] == "BoundaryFill":
            matches = [item for item in settings.get("tools", [])
                       if item["selection_record_object_id"] == selected["selection_record_object_id"]]
            if (len(matches) == 1 and matches[0]["kind"] == "Body"
                    and ids == [matches[0]["descriptor_object_id"]]):
                return "BodyTool", "Decoded explicit Boundary Fill body-tool partition agrees with the selected descriptor"
        return "OwnedBodySelection", "Owned referenced body selection; operation-specific input role remains unresolved"

    for owner_id, selections in by_owner.items():
        feature = feature_map.get(owner_id)
        if feature is None:
            unresolved.append({"object_id": owner_id, "kind": "FeatureBodyInputs",
                               "reason": "Body selection owner is not a recognized named feature"})
            continue
        try:
            feature_record = primary.get(owner_id)
            if feature_record is None or feature_record.class_guid != feature["class_guid"]:
                raise ValueError("Feature identity/class disagrees with its primary record")
            selected_ids = [item["selection_record_object_id"] for item in selections]
            if len(set(selected_ids)) != len(selected_ids):
                raise ValueError("Duplicate owned body selection entries")
            required, groups = set(), []
            for selection in selections:
                selection_id = selection["selection_record_object_id"]
                _, payload = typed(selection_id, PROXY)
                if payload[0] != 0 or payload[1] not in (0, 1):
                    raise ValueError("Unsupported owned body proxy prefix")
                cursor = attributes(payload, 2)[1] if payload[1] else 2
                count = struct.unpack_from("<I", payload, cursor)[0]
                if not 1 <= count <= 1024:
                    raise ValueError("Unsupported owned body proxy descriptor count")
                identities = [reference(payload, cursor+4+11*i) for i in range(count)]
                if (identities != selection["descriptor_object_ids"]
                        or reference(payload, len(payload)-11) != owner_id):
                    raise ValueError("Body proxy descriptor list or owner disagrees with decoded selection")
                bodies = []
                for identity in identities:
                    _, definition = typed(identity, DESCRIPTOR)
                    descriptor = descriptors.get(identity)
                    if (descriptor is None or descriptor["owner_object_id"] != owner_id
                            or reference(definition, len(definition)-11) != owner_id):
                        raise ValueError("Body input descriptor owner disagrees with feature")
                    bodies.append({"native_body_object_id": descriptor["native_body_object_id"],
                                   "descriptor_object_id": identity,
                                   "body_anchor_object_id": descriptor["body_anchor_object_id"],
                                   "source_owner_object_id": descriptor["source_owner_object_id"],
                                   "body_properties": descriptor["body_properties"]})
                if [body["native_body_object_id"] for body in bodies] != selection["native_body_object_ids"]:
                    raise ValueError("Body proxy identities disagree with decoded descriptors")
                role, role_evidence = explicit_role(feature, selection)
                groups.append({"selection_record_object_id": selection_id,
                               "descriptor_object_ids": identities, "bodies": bodies,
                               "role": role, "role_evidence": role_evidence})
                required.update([selection_id]+identities)
            payload = data[feature_record.body:feature_record.end]
            table = reference_table(payload, feature, required)
            table["record_offset"] = feature_record.body+table["relative_offset"]
            groups.sort(key=lambda group: table["object_ids"].index(group["selection_record_object_id"]))
            selected_ids = [group["selection_record_object_id"] for group in groups]
            all_bodies = list(dict.fromkeys(body["native_body_object_id"] for group in groups for body in group["bodies"]))
            decoded.append({"feature_object_id": owner_id, "kind": feature["kind"], "name": feature.get("name"),
                            "selection_record_object_ids": selected_ids,
                            "native_body_object_ids": all_bodies, "body_selection_groups": groups,
                            "feature_reference_table": table,
                            "association": "Feature counted table references the selected proxies/descriptors; reciprocal proxy/descriptor owner references agree",
                            "coverage": "Observed body selection groups only; absence of other body/face/edge inputs is not established",
                            "lifecycle_status": "Explicit selected identities retained; historical inputs are not replaced with resulting bodies"})
        except (ValueError, UnicodeError, KeyError, IndexError, struct.error) as error:
            unresolved.append({"object_id": owner_id, "kind": "FeatureBodyInputs", "reason": str(error)})
    return {"decoded": decoded, "unresolved": unresolved,
            "scope": "Explicit feature-level body selection associations; operation-specific roles require separately decoded explicit input lists"}
