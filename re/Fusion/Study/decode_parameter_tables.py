"""Observed native parameter collections and names for model/user parameters.

Names resolve through reciprocal typed records, never through substring matches
in expressions. Expression dependency and evaluation semantics remain unknown.
"""

from collections import Counter
import struct

from decode_parameters import read_string
from decode_sketch import reference

COLLECTION = "B0556F58-EE09-46A7-B18F-E296F48E5B13"
NAMES = "E276745D-D84E-40D5-88BC-8C94DD4ACCDF"
NUMERIC = "7A6A3D31-BE74-4E19-9115-20642944C2E4"


def decode_parameter_tables(data, records, parameters):
    primary = {}
    for record in records:
        if record.is_primary:
            primary.setdefault(record.object_id, []).append(record)
    by_id = {}
    for parameter in parameters:
        by_id.setdefault(parameter["parameter_object_id"], []).append(parameter)

    def typed(identity, guid):
        choices = [r for r in primary.get(identity, []) if r.class_guid == guid]
        if len(choices) != 1:
            raise ValueError("Parameter table reference is unresolved or ambiguous")
        record = choices[0]
        return record, data[record.body:record.end]

    decoded, unresolved, users = [], [], []
    for record in records:
        if not record.is_primary or record.class_guid != COLLECTION:
            continue
        try:
            body = data[record.body:record.end]
            if len(body) < 42 or body[:11] != bytes(11) or body[26] != 0:
                raise ValueError("Unsupported parameter collection header")
            count = struct.unpack_from("<I", body, 27)[0]
            if count > 100000 or len(body) != 42+11*count:
                raise ValueError("Unsupported parameter collection count or extent")
            registry_id = reference(body, 15)
            member_ids = [reference(body, 31+11*i) for i in range(count)]
            if len(set(member_ids)) != count:
                raise ValueError("Duplicate parameter collection member")
            owner_id = reference(body, len(body)-11)
            if len(primary.get(owner_id, [])) != 1:
                raise ValueError("Parameter collection owner is unresolved or ambiguous")
            _, registry = typed(registry_id, NAMES)
            if len(registry) < 10 or registry[0] != 1:
                raise ValueError("Unsupported parameter name registry header")
            dependency_count = struct.unpack_from("<I", registry, 1)[0]
            cursor = 5+15*dependency_count
            if dependency_count != count+1 or cursor+5 > len(registry) or registry[cursor] != 0:
                raise ValueError("Parameter name registry dependency count disagrees")
            dependencies = [reference(registry, 5+15*i) for i in range(dependency_count)]
            if any(registry[16+15*i:20+15*i] != bytes(4) for i in range(dependency_count)):
                raise ValueError("Unsupported parameter registry dependency slots")
            if dependencies[0] != record.object_id or Counter(dependencies[1:]) != Counter(member_ids):
                raise ValueError("Parameter registry does not reciprocate collection membership")
            names_count = struct.unpack_from("<I", registry, cursor+1)[0]
            if names_count != count:
                raise ValueError("Parameter registry name count disagrees")
            cursor += 5
            entries = []
            for _ in range(names_count):
                name, cursor = read_string(registry, cursor)
                identity = reference(registry, cursor)
                cursor += 11
                entries.append((name, identity))
            if (cursor != len(registry) or len({n for n, _ in entries}) != count
                    or Counter(i for _, i in entries) != Counter(member_ids)):
                raise ValueError("Parameter name table membership or extent disagrees")
            members = []
            local_users = []
            for name, identity in entries:
                _, raw = typed(identity, NUMERIC)
                choices = by_id.get(identity, [])
                if not choices:
                    raise ValueError("Parameter table member has no successfully decoded parameter record")
                if len(choices) != 1:
                    raise ValueError("Parameter table member resolves to ambiguous decoded parameter records")
                if choices[0]["parameter_name"] != name:
                    raise ValueError("Parameter table name does not match its decoded parameter record")
                parameter = choices[0]
                if raw[-12] != 0 or reference(raw, len(raw)-11) != record.object_id:
                    raise ValueError("Parameter does not reciprocate collection ownership")
                kind = parameter.get("parameter_kind", "ModelParameter")
                members.append({"parameter_name": name, "parameter_object_id": identity,
                                "parameter_kind": kind,
                                "binding_object_id": parameter["declared_binding_object_id"]})
                if kind == "UserParameter":
                    local_users.append({**parameter, "collection_object_id": record.object_id,
                                        "collection_owner_object_id": owner_id,
                                        "name_registry_object_id": registry_id,
                                        "expression_status": "Stored expression and cached value; not evaluated"})
            # Registry order differs from collection order; retain both explicitly.
            decoded.append({"collection_object_id": record.object_id,
                            "collection_owner_object_id": owner_id,
                            "name_registry_object_id": registry_id,
                            "stored_header_counter": struct.unpack_from("<I", body, 11)[0],
                            "member_object_ids": member_ids, "named_members": members})
            users.extend(local_users)
        except (ValueError, UnicodeError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "reason": str(error)})
    return {"decoded": decoded, "user_parameters": users, "unresolved": unresolved,
            "scope": "Observed parameter collection membership, names and reciprocal ownership; numeric/Text model and user variants",
            "limitations": ["Expression evaluation and explicit expression dependency edges are unresolved",
                            "Other parameter types, name variants, other control characters and unobserved favorite flags are unverified"]}
