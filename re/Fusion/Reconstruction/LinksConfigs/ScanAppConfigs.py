"""Scan the Fusion app bundle for configured designs.

Usage: python3.14 -I ScanAppConfigs.py <Autodesk Fusion.app/Contents> <output.json>

The scan is read-only. It records paths relative to the bundle only.
"""

import collections
import io
import json
import sys
import zipfile
from pathlib import Path

DESIGN_SUFFIXES = (".f3d", ".f3z")
SIDECAR_PREFIXES = ("DesignConfigurationTable", "DesignConfigurationRule")
SIDECAR_SUFFIXES = (".dsgcfg", ".dsgcfgrule")
STUB_FILES = (
    "Api/Python/packages/adsk/defs/adsk/fusion.py",
    "Api/Python/packages/adsk/defs/adsk/core.py",
)
STUB_NAMES = (
    "createConfiguredDesign",
    "isConfiguredDesign",
    "configurationTopTable",
    "addFromConfiguration",
    "addFromCustomConfiguration",
    "configuredDataFile",
)


def is_sidecar(name):
    base = name.rsplit("/", 1)[-1]
    return base.startswith(SIDECAR_PREFIXES) or base.endswith(SIDECAR_SUFFIXES)


def scan_archive(data, label, report):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist():
            if is_sidecar(info.filename):
                report["sidecars"] += 1
                report["sidecar_sizes"][str(info.file_size)] += 1
                if info.file_size > 2:
                    report["large_sidecars"].append([label, info.filename, info.file_size])
            if info.filename.lower().endswith(".f3d"):
                report["nested_designs"] += 1
                scan_archive(archive.read(info), f"{label}!{info.filename}", report)


def scan_designs(contents):
    report = {
        "design_files": 0,
        "nested_designs": 0,
        "open_errors": [],
        "sidecars": 0,
        "sidecar_sizes": collections.Counter(),
        "large_sidecars": [],
        "folders": collections.Counter(),
    }
    for path in sorted(contents.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in DESIGN_SUFFIXES:
            continue
        label = path.relative_to(contents).as_posix()
        report["design_files"] += 1
        report["folders"][str(Path(label).parent)] += 1
        try:
            scan_archive(path.read_bytes(), label, report)
        except (zipfile.BadZipFile, OSError, ValueError) as error:
            report["open_errors"].append([label, type(error).__name__])
    report["sidecar_sizes"] = dict(report["sidecar_sizes"])
    report["folders"] = dict(report["folders"].most_common())
    return report


def scan_stubs(contents):
    found = {}
    for relative in STUB_FILES:
        path = contents / relative
        text = path.read_text(errors="replace") if path.exists() else ""
        found[relative] = {name: text.count(f"def {name}") for name in STUB_NAMES}
    return found


def main():
    contents = Path(sys.argv[1])
    output = Path(sys.argv[2])
    result = {
        "scope": "Fusion app bundle Contents folder, read-only",
        "designs": scan_designs(contents),
        "api_stubs": scan_stubs(contents),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
