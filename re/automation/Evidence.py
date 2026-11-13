import json
import posixpath
import re
from pathlib import PurePosixPath

NATIVE_SUFFIXES = (".f3d", ".f3z", ".sldprt", ".sldasm", ".fcstd")


def resolve_candidates(path, name, native_paths):
    if name.startswith("/") or re.match(r"[A-Za-z]:/", name):
        return []
    candidates = []
    directory = posixpath.dirname(path)
    while True:
        candidate = posixpath.normpath(posixpath.join(directory, name))
        if candidate in native_paths and candidate not in candidates:
            candidates.append(candidate)
        if not directory:
            return candidates
        directory = posixpath.dirname(directory)


def inspect_evidence(path, content, native_paths):
    if len(content) > 32 * 1024 * 1024:
        raise ValueError("evidence JSON exceeds 32 MiB")
    data = json.loads(content)
    references = []
    measurements = []
    builds = []
    fields = {
        "body_count", "result_body_count", "solid_body_count", "volume_mm3", "volume_cm3",
        "volume_m3", "volume", "centre_mm", "center_mm", "center_of_mass", "centre_of_mass",
        "center_of_mass_cm", "surface_area_mm2", "rebuilt", "opened", "load_errors", "load_warnings",
    }

    def record_reference(text, pointer, recorded_as):
        if not isinstance(text, str):
            return
        name = text.replace("\\", "/")
        if PurePosixPath(name).suffix.lower() not in NATIVE_SUFFIXES:
            return
        candidates = resolve_candidates(path, name, native_paths)
        references.append({
            "pointer": pointer,
            "recorded_as": recorded_as,
            "recorded_path": text,
            "candidate_paths": candidates,
            "association": "relative_path_only" if candidates else "unavailable_or_unbound",
            "capture_hash_binding": "not_established",
        })

    def walk(value, pointer=""):
        if isinstance(value, list):
            for index, child in enumerate(value):
                location = f"{pointer}/{index}"
                record_reference(child, location, "value")
                walk(child, location)
        elif isinstance(value, dict):
            for key, child in value.items():
                location = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
                if key in ("fusion_version", "solidworks_version", "application_build"):
                    builds.append({"pointer": location, "value": child})
                if key in fields:
                    measurements.append({
                        "pointer": location,
                        "value": child,
                        "classification": "expected" if any(
                            part in ("requested", "expected", "expected_geometry")
                            for part in location.split("/")
                        ) else "recorded_unqualified",
                    })
                record_reference(key, location, "member_name")
                record_reference(child, location, "value")
                walk(child, location)

    walk(data)
    return {
        "path": path,
        "application_builds": builds,
        "references": references,
        "measurements": measurements,
        "qualification": "historical_observations_only",
    }
