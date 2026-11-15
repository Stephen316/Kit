import re

from Records import label

MAX_OUTPUT_BYTES = 256 * 1024 * 1024


class InvalidOutput(ValueError):
    pass


def output_manifest(value, paths=True):
    if not isinstance(value, dict) or len(value) > 64:
        raise ValueError("output artifacts must map at most 64 roles")
    total = 0
    for role, item in value.items():
        label(role)
        if not isinstance(item, dict) or set(item) != ({"path", "sha256", "size_bytes"} if paths else {"sha256", "size_bytes"}):
            raise ValueError("output artifact fields must match the version 1 manifest")
        if not isinstance(item["sha256"], str) or not re.fullmatch("[0-9a-f]{64}", item["sha256"]):
            raise ValueError("output digest must be a lowercase SHA-256")
        if type(item["size_bytes"]) is not int or not 0 <= item["size_bytes"] <= MAX_OUTPUT_BYTES:
            raise ValueError("output size must be between zero and 256 MiB")
        total += item["size_bytes"]
        if paths:
            path = item["path"]
            if not isinstance(path, str) or not 1 <= len(path) <= 4096 or any(ord(char) < 32 or char in '\\:*?"<>|' for char in path):
                raise ValueError("output path must be a relative slash-separated path")
            if any(not part or part in (".", "..") or part.rstrip(" .") != part for part in path.split("/")):
                raise ValueError("output path contains an unsafe component")
            if any(part.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$", *(f"COM{index}" for index in range(1, 10)), *(f"LPT{index}" for index in range(1, 10))} for part in path.split("/")):
                raise ValueError("output path contains a Windows device name")
    if total > MAX_OUTPUT_BYTES:
        raise ValueError("declared outputs exceed 256 MiB in aggregate")
    return value
