import re
from pathlib import Path

from Records import bounded, label, read_record
from OutputManifest import output_manifest

SCHEMA_KEYS = {"$schema", "title", "description", "type", "properties", "required", "additionalProperties", "items", "enum", "const", "minLength", "maxLength", "minimum", "maximum", "minItems", "maxItems"}
TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}
OUTCOMES = {"completed", "rejected", "waiting_evidence", "waiting_ci", "waiting_application"}
ENTRY_KEYS = {"pool", "argv", "result_schema", "threads", "initial_peak_memory_mib", "max_memory_mib"}


def check_schema(schema, depth=0):
    if depth > 32 or not isinstance(schema, dict) or schema.keys() - SCHEMA_KEYS:
        raise ValueError("result schema uses an unsupported keyword or nesting")
    kinds = schema.get("type", [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    if not isinstance(kinds, list) or not set(kinds) <= TYPES:
        raise ValueError("result schema type is not supported")
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise ValueError("result schema properties must be an object")
    for child in properties.values():
        check_schema(child, depth + 1)
    required = schema.get("required", [])
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        raise ValueError("result schema required must list property names")
    extra = schema.get("additionalProperties", True)
    if isinstance(extra, dict):
        check_schema(extra, depth + 1)
    elif not isinstance(extra, bool):
        raise ValueError("result schema additionalProperties must be a boolean or schema")
    if "items" in schema:
        check_schema(schema["items"], depth + 1)
    if "enum" in schema and not isinstance(schema["enum"], list):
        raise ValueError("result schema enum must be an array")
    for key in ("minLength", "maxLength", "minItems", "maxItems"):
        if key in schema and (type(schema[key]) is not int or schema[key] < 0):
            raise ValueError(f"result schema {key} must be a non-negative integer")
    for key in ("minimum", "maximum"):
        if key in schema and (type(schema[key]) not in (int, float)):
            raise ValueError(f"result schema {key} must be a number")
    return schema


def type_matches(value, kind):
    if kind == "object":
        return isinstance(value, dict)
    if kind == "array":
        return isinstance(value, list)
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        return type(value) is int
    if kind == "number":
        return type(value) in (int, float)
    if kind == "boolean":
        return type(value) is bool
    return value is None


def conformance(value, schema, path="$"):
    kinds = schema.get("type", [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    if kinds and not any(type_matches(value, kind) for kind in kinds):
        return f"{path} must have type {'/'.join(kinds)}"
    if "const" in schema and value != schema["const"]:
        return f"{path} must equal its constant"
    if "enum" in schema and value not in schema["enum"]:
        return f"{path} is not an allowed value"
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", len(value)):
            return f"{path} has an unsupported length"
    if type(value) in (int, float):
        if value < schema.get("minimum", value) or value > schema.get("maximum", value):
            return f"{path} is outside its range"
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", len(value)):
            return f"{path} has an unsupported item count"
        if "items" in schema:
            for index, item in enumerate(value):
                error = conformance(item, schema["items"], f"{path}[{index}]")
                if error:
                    return error
    if isinstance(value, dict):
        for name in schema.get("required", []):
            if name not in value:
                return f"{path}.{name} is required"
        properties = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for name, item in value.items():
            if name in properties:
                error = conformance(item, properties[name], f"{path}.{name}")
            elif extra is False:
                error = f"{path}.{name} is not allowed"
            elif isinstance(extra, dict):
                error = conformance(item, extra, f"{path}.{name}")
            else:
                error = None
            if error:
                return error
    return None


def result_error(value, schema):
    if not isinstance(value, dict) or not {"outcome", "reason", "records"} <= value.keys() or value.keys() - {"outcome", "reason", "records", "artifacts"}:
        return "result must contain outcome, reason, records and optional artifacts"
    if value["outcome"] not in OUTCOMES:
        return "result outcome is not a runner outcome"
    if not isinstance(value["reason"], str) or not 1 <= len(value["reason"]) <= 2048:
        return "result reason must contain 1–2048 characters"
    if "artifacts" in value:
        if value["outcome"] != "completed":
            return "only a completed result may declare output artifacts"
        try:
            output_manifest(value["artifacts"])
        except ValueError as error:
            return str(error)
    return conformance(value["records"], schema, "$.records")


class Registry:
    def __init__(self, path, root):
        path = Path(path).resolve()
        record = read_record(path)
        if set(record) != {"runners"} or not isinstance(record["runners"], dict) or not 1 <= len(record["runners"]) <= 256:
            raise ValueError("runner registry must contain only 1–256 runners")
        self.runners = {}
        for kind, entry in record["runners"].items():
            label(kind)
            if not isinstance(entry, dict) or not {"pool", "argv", "result_schema"} <= entry.keys() or entry.keys() - ENTRY_KEYS:
                raise ValueError(f"runner {kind} fields do not match the version 1 registry")
            argv = entry["argv"]
            if not isinstance(argv, list) or not 1 <= len(argv) <= 64 or not all(isinstance(item, str) and 1 <= len(item) <= 4096 and "\0" not in item for item in argv):
                raise ValueError(f"runner {kind} argv must list 1–64 non-empty strings")
            if any("{" in item and item != "{session}" for item in argv):
                raise ValueError(f"runner {kind} argv permits only the whole-argument {{session}} substitution")
            schema_path = Path(entry["result_schema"])
            schema_path = (schema_path if schema_path.is_absolute() else Path(root) / schema_path).resolve()
            schema = check_schema(read_record(schema_path))
            estimate = bounded(entry.get("initial_peak_memory_mib", 1024), 1, 1048576)
            self.runners[kind] = {
                "pool": label(entry["pool"]),
                "argv": list(argv),
                "schema": schema,
                "schema_path": str(schema_path),
                "threads": bounded(entry.get("threads", 1), 1, 256),
                "initial_peak_memory_mib": estimate,
                "max_memory_mib": bounded(entry.get("max_memory_mib", min(1048576, estimate * 2)), 1, 1048576),
            }

    def pools(self):
        result = {}
        for kind, entry in self.runners.items():
            result.setdefault(entry["pool"], []).append(kind)
        return {name: sorted(kinds) for name, kinds in result.items()}

    def argv(self, kind, session):
        return [str(session) if item == "{session}" else item for item in self.runners[kind]["argv"]]


def safe_name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("input digest must be a lowercase SHA-256")
    return value
