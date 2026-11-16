import subprocess
from pathlib import Path
from types import SimpleNamespace

from ApplicationProtocol import (
    encoded,
    file_bytes,
    macos_automatic_quit,
    owner_lock,
    require,
    sha256,
)
from FusionPhaseBAcknowledgement import acknowledgement_drained
from FusionRestartPairs import bound_pair, open_pair, pair_for, release_pair
from Ledger import Ledger
from StoreRead import read_store

ROOT = Path(__file__).resolve().parents[3]
POLICY_FILES = (
    "Adapters.py",
    "ApplicationAckIntent.py",
    "Controller.py",
    "FusionAcknowledgementRetry.py",
    "FusionRestartPairs.py",
    "GroupClaims.py",
    "Ledger.py",
    "PriorityClaims.py",
    "RecoveryFence.py",
    "SingleClaim.py",
    "Supervisor.py",
    "ApplicationWorkers/FusionLifecycleRegistration.py",
    "ApplicationWorkers/FusionLifecycleOwner.py",
    "ApplicationWorkers/FusionPhaseBAcknowledgement.py",
    "ApplicationWorkers/QueueFusionPhases.py",
)


def installation_pin(config):
    return sha256(encoded(config))


def checked_policy(config, resource, *, extra=()):
    require(
        macos_automatic_quit(config)
        and resource == f"application:{config['installation']}"
        and Path(config["source_root"]).resolve(strict=True) == ROOT,
        "automatic reservation requires the same pinned macOS owner controller and installation",
    )
    for name in (*POLICY_FILES, *extra):
        relative = f"re/automation/{name}"
        source = subprocess.run(
            [
                "git",
                "--no-replace-objects",
                "-C",
                str(ROOT),
                "cat-file",
                "blob",
                f"{config['source_revision']}:{relative}",
            ],
            capture_output=True,
            check=False,
            timeout=15,
        )
        require(
            source.returncode == 0
            and source.stdout
            and file_bytes(ROOT / relative) == source.stdout,
            "automatic reservation requires the reviewed controller and supervisor source policy",
        )
    return installation_pin(config)


def pending_admission(store, queue, config, active, final_path):
    with read_store(store / "ledger.sqlite3", None, (4,)) as database:
        ledger = SimpleNamespace(db=database)
        if pair_for(ledger, queue["jobs"]["a"]) is None:
            return False
        pair = bound_pair(ledger, queue, installation_pin(config), active)
        if pair["restart_intent"] is None:
            return True
        require(
            pair["restart_intent"] == active["restart_intent_sha256"],
            "Fusion restart reservation already belongs to another accepted intent",
        )
        if pair["final_evidence"] is not None:
            require(
                sha256(file_bytes(final_path)) == pair["final_evidence"],
                "released Fusion reservation lost its exact final evidence",
            )
        return False


def admit(store, queue, config, active):
    with Ledger(store) as ledger:
        open_pair(ledger, queue, installation_pin(config), active)


def release(
    store, queue, config, active, final_path, final_bytes, *, supervisor_state, final
):
    with read_store(store / "ledger.sqlite3", None, (4,)) as database:
        if pair_for(SimpleNamespace(db=database), queue["jobs"]["a"]) is None:
            return True
    with owner_lock(final_path.parent / "dispatch.lock"):
        with Ledger(store) as ledger:
            require(
                file_bytes(final_path) == final_bytes,
                "final Fusion lifecycle receipt changed",
            )
            pin = installation_pin(config)
            pair = bound_pair(ledger, queue, pin, active)
            if pair["final_evidence"] is None and not acknowledgement_drained(
                final_path.parent, supervisor_state, ledger, pair, final["phase_b"]
            ):
                return False
            release_pair(ledger, queue, pin, active, final_bytes)
    return True
