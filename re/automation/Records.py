import hashlib
import json
import re
from pathlib import Path


def canonical(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    if len(encoded.encode("utf-8")) > 1024 * 1024:
        raise ValueError("metadata exceeds 1 MiB")
    return encoded


def read_record(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError("record must be a regular JSON file no larger than 1 MiB")
    with path.open("rb") as source:
        content = source.read(1024 * 1024 + 1)
    if len(content) > 1024 * 1024:
        raise ValueError("record exceeds 1 MiB")
    value = json.loads(content.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("record must be a JSON object")
    canonical(value)
    return value


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def label(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,127}", value):
        raise ValueError("labels must contain 1–128 ASCII identifier characters")
    return value


def bounded(value, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"integer must be between {lower} and {upper}")
    return value


def specification(value):
    required = {"id", "kind", "inputs", "rule_version", "tool_version"}
    optional = {"depends_on", "resources", "options", "max_attempts", "lease_seconds", "timeout_seconds", "retry_base_seconds"}
    if not isinstance(value, dict) or not required <= value.keys() or value.keys() - required - optional:
        raise ValueError("job fields do not match the version 1 contract")
    if not isinstance(value["inputs"], dict) or len(value["inputs"]) > 64:
        raise ValueError("inputs must map at most 64 roles to named evidence bindings")
    result = {key: label(value[key]) for key in ("id", "kind", "rule_version", "tool_version")}
    result["inputs"] = {label(role): label(name) for role, name in value["inputs"].items()}
    for key in ("depends_on", "resources"):
        items = value.get(key, [])
        if not isinstance(items, list) or len(items) > 64:
            raise ValueError(f"{key} must be an array with at most 64 labels")
        result[key] = sorted({label(item) for item in items})
    if result["id"] in result["depends_on"]:
        raise ValueError("job cannot depend on itself")
    options = value.get("options", {})
    if not isinstance(options, dict):
        raise ValueError("options must be a JSON object")
    result["options"] = options
    for key, default, lower, upper in (
        ("max_attempts", 3, 1, 20),
        ("lease_seconds", 60, 1, 3600),
        ("timeout_seconds", 300, 1, 86400),
        ("retry_base_seconds", 1, 1, 60),
    ):
        result[key] = bounded(value.get(key, default), lower, upper)
    if result["lease_seconds"] > result["timeout_seconds"]:
        raise ValueError("lease cannot exceed the execution timeout")
    if len(canonical(result).encode("utf-8")) > 64 * 1024:
        raise ValueError("job definition exceeds 64 KiB")
    return result


def reason_text(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 2048:
        raise ValueError("reason must contain 1–2048 characters")
    return value
