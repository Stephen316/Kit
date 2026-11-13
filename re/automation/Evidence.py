import json
from pathlib import PurePosixPath


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

    def walk(value, pointer=""):
        if isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{pointer}/{index}")
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
                if isinstance(child, str) and PurePosixPath(child.replace("\\", "/")).suffix.lower() in (
                    ".f3d", ".f3z", ".sldprt", ".sldasm", ".fcstd"
                ):
                    name = child.replace("\\", "/")
                    candidate = str(PurePosixPath(path).parent / name)
                    candidates = [candidate] if candidate in native_paths else []
                    if name in native_paths:
                        candidates = [name]
                    references.append({
                        "pointer": location,
                        "recorded_path": child,
                        "candidate_paths": candidates,
                        "association": "relative_path_only" if candidates else "unavailable_or_unbound",
                        "capture_hash_binding": "not_established",
                    })
                walk(child, location)

    walk(data)
    return {
        "path": path,
        "application_builds": builds,
        "references": references,
        "measurements": measurements,
        "qualification": "historical_observations_only",
    }
