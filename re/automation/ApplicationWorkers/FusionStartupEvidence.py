import json
import os
import re
import threading
import time
from pathlib import Path

PROFILE_SCOPE = "owner_fusion_bootstrap_startup"
REQUEST_SCOPE = "fusion_bootstrap_startup_challenge"
RECEIPT_SCOPE = "fusion_bootstrap_startup_observation"
MAILBOX = "bootstrap-startup"
ACTIVE = "active.json"
ADDIN = "KitCaptureRunner"
ADDIN_ID = "86fe0da5-2159-46d0-b155-75b61d237365"
MAX_SECONDS = 30


def starting_manifest(protocol, original):
    document = json.loads(original)
    protocol["require"](
        document["autodeskProduct"] == "Fusion360"
        and document["type"] == "addin"
        and document["id"] == ADDIN_ID
        and document["runOnStartup"] is False
        and document["supportedOS"] == "windows|mac",
        "unexpected tracked Fusion add-in manifest",
    )
    return protocol["encoded"]({**document, "runOnStartup": True})


def executable_peer(read_peer, pid):
    peer = read_peer(pid)
    return {**peer, "executable": os.fspath(peer["executable"])}


def expected_profile(
    protocol, config, installation, lifecycle_hash, installed, executable
):
    source = protocol["committed_bytes"]
    digest = protocol["sha256"]
    manifest = starting_manifest(protocol, source(config, protocol["STARTUP_MANIFEST"]))
    bootstrap = source(config, protocol["BOOTSTRAP"])
    profile = {
        "version": 1,
        "scope": PROFILE_SCOPE,
        "installation_sha256": digest(installation),
        "lifecycle_sha256": lifecycle_hash,
        "installation": config["installation"],
        "source_revision": config["source_revision"],
        "installed_bootstrap": os.fspath(installed),
        "executable": os.fspath(executable),
        "manifest_sha256": digest(manifest),
        "bootstrap_sha256": digest(bootstrap),
        "protocol_sha256": digest(source(config, protocol["PROTOCOL"])),
        "startup_provider_sha256": digest(
            source(config, protocol["MAC_STARTUP_EVIDENCE"])
        ),
    }
    return profile, bootstrap, manifest


def profile_input(protocol, path):
    directory = protocol["directory"](path.parent)
    raw = protocol["file_bytes"](directory / path.name)
    profile = json.loads(raw)
    protocol["require"](
        type(profile["version"]) is int
        and profile["version"] == 1
        and profile["scope"] == PROFILE_SCOPE
        and isinstance(profile["lifecycle_sha256"], str)
        and re.fullmatch("[0-9a-f]{64}", profile["lifecycle_sha256"]),
        "invalid Fusion startup profile",
    )
    return raw, profile


def installed_path(protocol, path):
    protocol["require"](
        path.is_absolute() and path.parent.name == ADDIN and path.name == f"{ADDIN}.py",
        "startup profile needs the exact installed add-in path",
    )
    return protocol["directory"](path.parent) / path.name


def verified_profile(
    protocol,
    config,
    installation,
    path,
    installed,
    lifecycle_hash,
    executable,
):
    raw, profile = profile_input(protocol, path)
    installed = installed_path(protocol, installed)
    expected, bootstrap, manifest = expected_profile(
        protocol, config, installation, lifecycle_hash, installed, executable
    )
    protocol["require"](
        profile == expected
        and protocol["file_bytes"](installed) == bootstrap
        and protocol["file_bytes"](installed.with_suffix(".manifest")) == manifest,
        "Fusion startup profile or installed add-in bytes differ from the pinned deployment",
    )
    return raw, profile


def response_path(root, challenge):
    if not isinstance(challenge, str) or not re.fullmatch("[0-9a-f]{48}", challenge):
        raise ValueError("invalid Fusion startup challenge")
    return root / f"{challenge}.response.json"


class Startup:
    def __init__(
        self,
        protocol,
        host,
        installation_path,
        installation,
        profile_path,
        bootstrap,
        main_thread,
        read_peer,
    ):
        self.protocol = protocol
        self.host = host
        self.installation_path = installation_path
        self.installation = installation
        self.profile_path = profile_path
        self.bootstrap = bootstrap
        self.main_thread = main_thread
        self.read_peer = read_peer
        self.root = protocol["directory"](host.root / MAILBOX, True)
        self.peer = executable_peer(read_peer, os.getpid())
        _, candidate = profile_input(protocol, profile_path)
        self.raw, self.profile = verified_profile(
            protocol,
            host.config,
            installation,
            profile_path,
            bootstrap,
            candidate["lifecycle_sha256"],
            self.peer["executable"],
        )
        self.profile_sha256 = protocol["sha256"](self.raw)

    def pending(self):
        try:
            raw = self.protocol["file_bytes"](self.root / ACTIVE)
            request = json.loads(raw)
            if self.matches(request) and not os.path.lexists(
                response_path(self.root, request["challenge"])
            ):
                return request["challenge"]
        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
            RecursionError,
        ):
            pass
        return None

    def matches(self, request):
        now = time.time()
        return (
            set(request)
            == {
                "version",
                "scope",
                "challenge",
                "profile_sha256",
                "peer",
                "client",
                "issued_at",
                "deadline",
            }
            and type(request["version"]) is int
            and request["version"] == 1
            and request["scope"] == REQUEST_SCOPE
            and request["profile_sha256"] == self.profile_sha256
            and request["peer"] == self.peer
            and request["client"] != self.peer
            and type(request["issued_at"]) in (int, float)
            and type(request["deadline"]) in (int, float)
            and request["issued_at"]
            <= now
            < request["deadline"]
            <= request["issued_at"] + MAX_SECONDS
        )

    def prove(self, challenge, app):
        protocol = self.protocol
        require = protocol["require"]
        require(
            threading.get_ident() == self.main_thread,
            "Fusion startup proof requires the add-in main thread",
        )
        path = self.root / ACTIVE
        raw = protocol["file_bytes"](path)
        request = json.loads(raw)
        require(
            self.matches(request) and request["challenge"] == challenge,
            "Fusion startup challenge changed",
        )
        response = response_path(self.root, challenge)
        require(
            protocol["file_bytes"](self.root / f"{challenge}.request.json") == raw,
            "Fusion startup challenge differs from its immutable request",
        )
        client = request["client"]
        require(
            client == executable_peer(self.read_peer, client["pid"]),
            "Fusion startup observer is no longer live",
        )
        if app.isStartupComplete is not True:
            return
        require(
            protocol["file_bytes"](self.installation_path) == self.installation
            and protocol["file_bytes"](self.profile_path) == self.raw
            and protocol["sha256"](protocol["file_bytes"](self.bootstrap))
            == self.profile["bootstrap_sha256"]
            and protocol["sha256"](
                protocol["file_bytes"](self.bootstrap.with_suffix(".manifest"))
            )
            == self.profile["manifest_sha256"]
            and self.peer == executable_peer(self.read_peer, os.getpid())
            and protocol["file_bytes"](path) == raw
            and self.matches(request)
            and isinstance(app.version, str)
            and 0 < len(app.version) <= 128,
            "Fusion startup custody changed before observation",
        )
        value = {
            "version": 1,
            "scope": RECEIPT_SCOPE,
            "profile_sha256": self.profile_sha256,
            "request_sha256": protocol["sha256"](raw),
            "peer": self.peer,
            "observed_at": time.time(),
            "source_revision": self.host.config["source_revision"],
            "startup_provider_sha256": self.profile["startup_provider_sha256"],
            "fusion_version": app.version,
            "startup_context": "vendor_application_startup",
        }
        require(
            value["observed_at"] < request["deadline"],
            "Fusion startup challenge expired",
        )
        protocol["write_new"](response, protocol["encoded"](value))
