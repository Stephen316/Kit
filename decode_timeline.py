"""Observed history sequence, groups, suppression and rollback state.

History order comes from explicit ordered references, not object IDs, record
offsets or each feature family's stored counter. Multiple history owners are
kept separate rather than guessed into one assembly timeline.
"""

import struct

from decode_parameters import read_string
from decode_sketch import reference


HISTORY_GUID = "2F4C1849-1A5A-4F6C-A086-8DD445CBF94B"
GROUP_GUID = "A917FE80-93D6-45AD-B741-93BB1ACA5E61"


def feature_state(body):
    if len(body) < 66:
        raise ValueError("Feature state footer is truncated")
    tail = body[-66:]
    if (tail[:5] != b"\0"*5 or tail[5] not in (0, 1) or tail[6] != 0 or tail[18] != 0
            or tail[23:27] != b"\x01\x01\0\0" or tail[35:39] != b"\x01\x01\0\0"
            or tail[50] != 1 or tail[51] != tail[5] or tail[52] not in (0, 1)
            or tail[64:] != b"\0\0"):
        raise ValueError("Unrecognized shared feature state footer")
    for offset in (7, 39, 53):
        reference(tail, offset)
    return {"is_suppressed": bool(tail[5]), "is_rolled_back": bool(tail[52]),
            "source": "Observed shared feature footer; suppression copies agree"}


def read_group(body, object_id):
    if body[:6] != b"\0\0\x01\0\0\0" or body[6] not in (0, 1):
        raise ValueError("Unrecognized history group prefix")
    count = struct.unpack_from("<I", body, 7)[0]
    if not 1 <= count <= 100000 or 11+11*count+6 > len(body):
        raise ValueError("Truncated history group members")
    members = [reference(body, 11+11*i) for i in range(count)]
    cursor = 11+11*count
    if body[cursor:cursor+2] != b"\0\0":
        raise ValueError("Unrecognized history group name separator")
    name, end = read_string(body, cursor+2)
    if end != len(body) or len(set(members)) != count:
        raise ValueError("Unrecognized history group suffix or duplicate members")
    return {"object_id": object_id, "name": name or None, "is_collapsed": not bool(body[6]),
            "member_feature_ids": members}


def decode_timeline(data, records, features):
    by_feature = {f["object_id"]: f for f in features}
    by_offset = {r.start: r for r in records}
    unresolved, groups, sequences = [], {}, []
    for feature in features:
        record = by_offset[feature["record_offset"]]
        try:
            feature["state"] = feature_state(data[record.body:record.end])
        except (ValueError, IndexError, struct.error) as error:
            unresolved.append({"object_id": feature["object_id"], "reason": str(error)})
    for record in records:
        if record.class_guid != GROUP_GUID:
            continue
        try:
            group = read_group(data[record.body:record.end], record.object_id)
            if record.object_id in groups:
                raise ValueError("Duplicate history group definition")
            groups[record.object_id] = group
        except (ValueError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "reason": str(error)})
    for record in records:
        if record.class_guid != HISTORY_GUID:
            continue
        body = data[record.body:record.end]
        try:
            if body[:2] != b"\0\0":
                raise ValueError("Unrecognized history sequence prefix")
            owner = reference(body, 2)
            count = struct.unpack_from("<I", body, 13)[0]
            if count > 100000 or len(body) != 17+11*count:
                raise ValueError("Unrecognized history sequence length")
            identities = [reference(body, 17+i*11) for i in range(count)]
            if len(set(identities)) != count:
                raise ValueError("Duplicate entries in history sequence")
            missing = [i for i in identities if i not in by_feature and i not in groups]
            if missing:
                raise ValueError("Unresolved history entries: "+str(missing))
            local_groups = {i: groups[i] for i in identities if i in groups}
            membership = {}
            for identity, group in local_groups.items():
                position = identities.index(identity)
                members = group["member_feature_ids"]
                if identities[position+1:position+1+len(members)] != members:
                    raise ValueError("Group members are not contiguous after their group entry")
                if any(i not in by_feature or i in membership for i in members):
                    raise ValueError("Unresolved, nested or overlapping history groups")
                membership.update({i: identity for i in members})
            history = [i for i in identities if i in by_feature]
            for index, identity in enumerate(history):
                by_feature[identity].update(history_index=index, history_owner_object_id=owner)
                if identity in membership:
                    by_feature[identity]["timeline_group_object_id"] = membership[identity]
            visible = []
            hidden = set()
            for identity in identities:
                if identity in hidden:
                    continue
                if identity in local_groups:
                    group = local_groups[identity]
                    if not group["is_collapsed"]:
                        continue
                    hidden.update(group["member_feature_ids"])
                    children = []
                    for child in group["member_feature_ids"]:
                        feature = by_feature[child]
                        feature["timeline_index"] = None
                        children.append({"object_id": child, "name": feature["name"], "kind": feature["kind"],
                                         "state": feature.get("state"), "timeline_index": None})
                    visible.append({"object_id": identity, "name": group["name"], "kind": "TimelineGroup",
                                    "timeline_index": len(visible), "children": children})
                else:
                    feature = by_feature[identity]
                    feature["timeline_index"] = len(visible)
                    visible.append({"object_id": identity, "name": feature["name"], "kind": feature["kind"],
                                    "state": feature.get("state"), "timeline_index": len(visible)})
            rollback = []
            for entry in visible:
                states = ([c.get("state") for c in entry["children"]] if "children" in entry else [entry.get("state")])
                flags = {s["is_rolled_back"] for s in states if s is not None}
                rollback.append(next(iter(flags)) if len(flags) == 1 and all(s is not None for s in states) else None)
            marker = None
            if all(flag is not None for flag in rollback):
                first = next((i for i, flag in enumerate(rollback) if flag), len(rollback))
                if not any(not flag for flag in rollback[first:]):
                    marker = first
            sequences.append({"history_record_object_id": record.object_id, "owner_object_id": owner,
                              "native_entry_object_ids": identities, "feature_order": history,
                              "groups": list(local_groups.values()), "visible_entries": visible,
                              "timeline_count": len(visible), "marker_position": marker,
                              "marker_source": "Derived from decoded rollback flags and group projection",
                              "scope": "Observed history owner; multiple owners are not merged"})
        except (ValueError, KeyError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "reason": str(error)})
    locations = {}
    for sequence in sequences:
        visible_indices = {entry["object_id"]: entry["timeline_index"] for entry in sequence["visible_entries"]}
        for index, identity in enumerate(sequence["feature_order"]):
            locations.setdefault(identity, []).append({"owner_object_id": sequence["owner_object_id"],
                                                       "history_index": index,
                                                       "timeline_index": visible_indices.get(identity)})
    for identity, entries in locations.items():
        if len(entries) > 1:
            feature = by_feature[identity]
            for key in ("history_index", "timeline_index", "history_owner_object_id", "timeline_group_object_id"):
                feature.pop(key, None)
            feature["history_locations"] = entries
    return {"sequences": sequences, "unresolved": unresolved,
            "scope": "Observed history lists, group projection and shared feature state only"}
