import json
import os
import plistlib
import re
from pathlib import Path

from ApplicationProtocol import MAX_BYTES, file_bytes, require, sha256


def pinned_bundle(raw, installation_digest):
    profile = json.loads(raw)
    require(
        type(profile) is dict
        and set(profile)
        == {
            "version",
            "installation_sha256",
            "bundle",
            "info_sha256",
            "executable_sha256",
        }
        and type(profile["version"]) is int
        and profile["version"] == 1
        and profile["installation_sha256"] == installation_digest
        and all(
            isinstance(profile[key], str)
            and re.fullmatch(r"[0-9a-f]{64}", profile[key])
            for key in ("info_sha256", "executable_sha256")
        ),
        "macOS lifecycle profile differs from the trusted installation",
    )
    bundle = Path(profile["bundle"])
    info_path = bundle / "Contents" / "Info.plist"
    require(
        bundle.is_absolute()
        and bundle.suffix == ".app"
        and bundle.is_dir()
        and info_path.resolve(strict=True) == info_path,
        "macOS lifecycle profile requires a physical application bundle",
    )
    info = file_bytes(info_path)
    require(sha256(info) == profile["info_sha256"], "macOS bundle plist pin differs")
    metadata = plistlib.loads(info)
    name = metadata["CFBundleExecutable"]
    identifier = metadata["CFBundleIdentifier"]
    require(
        metadata["CFBundlePackageType"] == "APPL"
        and isinstance(name, str)
        and 0 < len(name) <= 255
        and name not in (".", "..")
        and not any(char in name for char in ("/", "\\", "\0"))
        and isinstance(identifier, str)
        and re.fullmatch(r"[A-Za-z0-9.-]{1,255}", identifier),
        "macOS bundle plist lacks an exact application executable or identifier",
    )
    executable = bundle / "Contents" / "MacOS" / name
    require(
        executable.resolve(strict=True) == executable
        and os.access(executable, os.X_OK)
        and sha256(file_bytes(executable, MAX_BYTES)) == profile["executable_sha256"],
        "macOS application executable path or pin differs",
    )
    return {
        "bundle_identifier": identifier,
        "info_sha256": profile["info_sha256"],
        "executable_sha256": profile["executable_sha256"],
        "executable": executable,
    }
